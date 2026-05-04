"""Map geometry + hackathon catalog (static JSON) + shops CSV."""

import json
from pathlib import Path

from fastapi import APIRouter, Query

from app.core.graph.airport_data import NODES
from app.core.graph.load_layout import load_graph_bundle
from app.core.graph.node_mapper import resolve_to_graph_node_id
from app.services.facilities_loader import load_facilities_bom
from app.services.route_narrative import passenger_place_name
from app.services.shops_loader import load_shops_t2_l02

router = APIRouter()

_DATA = Path(__file__).resolve().parents[1] / "data"


def _group_facilities_by_graph_node(facilities: list[dict]) -> list[dict]:
    """One entry per graph node; each lists every facility tied to that node."""
    by: dict[str, list[dict]] = {}
    for row in facilities:
        gid = str(row.get("graph_node_id") or "").strip() or "_unassigned"
        by.setdefault(gid, []).append(row)
    for gid in by:
        by[gid].sort(
            key=lambda r: str(r.get("name_display", "")).lower(),
        )

    def sort_key(gid: str) -> str:
        if gid == "_unassigned":
            return "\uffff"
        meta = NODES.get(gid) or {}
        return str(meta.get("name") or gid).lower()

    out: list[dict] = []
    for gid in sorted(by.keys(), key=sort_key):
        meta = NODES.get(gid) or {}
        node_name = (
            meta.get("name")
            if gid in NODES
            else ("Unassigned (no graph node)" if gid == "_unassigned" else gid)
        )
        fl = by[gid]
        out.append(
            {
                "graph_node_id": gid,
                "node_name": node_name,
                "count": len(fl),
                "facilities": fl,
            }
        )
    return out


@router.get("/map")
def get_terminal_map():
    """Nodes with x/y for SVG + edges for optional drawing."""
    nodes_dict, edges_list, graph_meta = load_graph_bundle()
    nodes: list[dict] = []
    for nid, meta in nodes_dict.items():
        row = {"id": nid, **meta}
        row["passenger_name"] = passenger_place_name(row)
        nodes.append(row)
    edges = [{"from": a, "to": b, "minutes": m} for a, b, m in edges_list]
    return {"meta": graph_meta, "nodes": nodes, "edges": edges}


@router.get("/map/resolve-node")
def resolve_map_node(q: str = Query(..., description="RAG navigation id, alias, or graph node id")):
    """Map LLM ``airport_data`` navigation ids (e.g. node-t2-entrance) to walking-graph ids without editing source JSON."""
    gid, how = resolve_to_graph_node_id(q)
    meta = NODES.get(gid) if gid else None
    name = None
    if meta is not None and gid:
        row = dict(meta)
        row["id"] = gid
        name = passenger_place_name(row)
    return {"requested": q, "graph_node_id": gid, "resolution": how, "passenger_name": name}


@router.get("/catalog")
def get_airport_catalog():
    """Flights, F&B, retail, services, offers (mock)."""
    path = _DATA / "mumbai_t2_catalog.json"
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/shops")
def get_shops_t2(
    zone: str | None = Query(None, description="Filter by zone e.g. pier_ne"),
    category: str | None = Query(None, description="Filter by category e.g. cafe"),
):
    """
    Shop directory: names + normalized map coordinates (0–100) and optional `graph_node_id`
    (navigation node id). Level 3/4 rows align with CSMIA T2 shop/dine card locations; map
    positions around `t2_l03_postsec` / `t2_l04_postsec` are schematic.
    """
    shops = load_shops_t2_l02()
    if zone:
        z = zone.strip().lower()
        shops = [s for s in shops if str(s.get("zone", "")).lower() == z]
    if category:
        c = category.strip().lower()
        shops = [s for s in shops if str(s.get("category", "")).lower() == c]
    return {
        "meta": {
            "terminal": "T2",
            "coordinate_system": "normalized_xy_0_100",
            "csv": "shops_t2_l02.csv",
            "directory_refs": [
                "https://csmia-mumbai.adaniairports.com/en/shop-and-dine/shopping",
                "https://csmia-mumbai.adaniairports.com/en/shop-and-dine/dining",
            ],
            "regenerate": "python3 scripts/generate_csmia_shop_csv.py (pulls full Sitecore Dining/Search results)",
        },
        "count": len(shops),
        "shops": shops,
    }


@router.get("/facilities")
def get_airport_facilities(
    category: str | None = Query(
        None, description="Filter by category e.g. main_facilities, other_facilities_pranaam"
    ),
):
    """
    Airport facilities from CSMIA facilities page + Sitecore AirportServices/Search overlay.
    Each row has schematic map coordinates and a `graph_node_id` for routing context.
    Response includes `facilities_by_node`: every facility listed exactly once under its graph node.
    """
    facilities = load_facilities_bom()
    if category:
        c = category.strip().lower()
        facilities = [
            f for f in facilities if str(f.get("category", "")).lower() == c
        ]
    by_node = _group_facilities_by_graph_node(facilities)
    return {
        "meta": {
            "coordinate_system": "normalized_xy_0_100",
            "csv": "facilities_bom.csv",
            "directory_ref": "https://csmia-mumbai.adaniairports.com/en/airport-facilities",
            "regenerate": "python3 scripts/generate_csmia_facilities_csv.py",
        },
        "count": len(facilities),
        "facilities": facilities,
        "facilities_by_node": by_node,
    }
