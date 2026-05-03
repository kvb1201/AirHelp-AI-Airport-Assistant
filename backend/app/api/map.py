"""Map geometry + hackathon catalog (static JSON)."""

import json
from pathlib import Path

from fastapi import APIRouter

from app.core.graph.airport_data import EDGES, GRAPH_META, NODES

router = APIRouter()

_DATA = Path(__file__).resolve().parents[1] / "data"


@router.get("/map")
def get_terminal_map():
    """Nodes with x/y for SVG + edges for optional drawing."""
    nodes = [{"id": nid, **meta} for nid, meta in NODES.items()]
    edges = [{"from": a, "to": b, "minutes": m} for a, b, m in EDGES]
    return {"meta": GRAPH_META, "nodes": nodes, "edges": edges}


@router.get("/catalog")
def get_airport_catalog():
    """Flights, F&B, retail, services, offers (mock)."""
    path = _DATA / "mumbai_t2_catalog.json"
    return json.loads(path.read_text(encoding="utf-8"))
