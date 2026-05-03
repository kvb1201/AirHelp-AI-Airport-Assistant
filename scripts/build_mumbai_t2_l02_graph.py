#!/usr/bin/env python3
"""
Rebuild mumbai_t2_level02_graph.json from a hub-and-four-pier geometric model.

Coordinates are normalized 0–100 with origin top-left (SVG-style).
Aligned to T2 Level 2 butterfly: central hub + NW / NE / SW / SE circulation spines.

Run from repo root:
  python3 scripts/build_mumbai_t2_l02_graph.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "backend" / "app" / "data" / "mumbai_t2_level02_graph.json"

# Pier tips (approximate outer gate-lounge ends on the X)
TIP_NW = (10.0, 10.0)
TIP_NE = (90.0, 10.0)
TIP_SW = (10.0, 90.0)
TIP_SE = (90.0, 90.0)

# Where each pier yellow spine meets the central hub (shoulder points)
J_NW = (42.0, 40.0)
J_NE = (58.0, 40.0)
J_SW = (42.0, 56.0)
J_SE = (58.0, 56.0)

HUB_C = (50.0, 48.0)

# South landside axis (centerline)
ENTRANCE = (50.0, 86.0)
BAGGAGE = (50.0, 76.0)
SEC_INTL = (46.0, 68.0)
SEC_DOM = (54.0, 68.0)
SEC_MERGE = (50.0, 64.0)
POST_SEC = (50.0, 58.0)


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def lerp(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def minutes_for(a: tuple[float, float], b: tuple[float, float]) -> int:
    """Walk time from normalized map distance (calibrated for ~25 min end-to-end pier)."""
    return max(1, min(8, int(round(dist(a, b) * 0.42))))


def spine_nodes(prefix: str, pier: str, zone: str, start: tuple[float, float], end: tuple[float, float], n: int):
    """Collinear spine nodes from start (hub junction) toward end (tip)."""
    nodes = {}
    ids = []
    for i in range(n + 1):
        t = i / n
        p = lerp(start, end, t)
        nid = f"{prefix}_sp_{i:02d}"
        ids.append(nid)
        label = "Pier spine" if 0 < i < n else ("Hub junction" if i == 0 else "Gate lounge approach")
        nodes[nid] = {
            "name": f"{pier} spine — segment {i}/{n}",
            "kind": "corridor" if i < n else "gate",
            "zone": zone,
            "terminal": "T2",
            "floor": "L02",
            "x": round(p[0], 2),
            "y": round(p[1], 2),
            "_label": label,
        }
    # Rename last node human gate name
    last = ids[-1]
    gate_names = {
        "nw": "Gate lounge — NW pier (mock 65–72)",
        "ne": "Gate lounge — NE pier (mock 73–78)",
        "sw": "Gate lounge — SW pier (mock 79–84)",
        "se": "Gate lounge — SE pier (mock 85–90)",
    }
    nodes[last]["name"] = gate_names.get(zone.split("_")[-1], "Gate lounge")
    nodes[last]["kind"] = "gate"
    return nodes, ids


def offset_point(base: tuple[float, float], toward: tuple[float, float], perp: float) -> tuple[float, float]:
    """Perpendicular offset from spine for WC/F&B (small lateral shift)."""
    dx, dy = toward[0] - base[0], toward[1] - base[1]
    ln = math.hypot(dx, dy) or 1.0
    ux, uy = dx / ln, dy / ln
    px, py = -uy, ux  # left normal
    return (base[0] + px * perp, base[1] + py * perp)


def main() -> None:
    nodes: dict = {}
    edges: list[list] = []

    meta = {
        "airport": "BOM",
        "airport_name": "Chhatrapati Shivaji Maharaj International Airport",
        "terminal": "T2",
        "floor": "L02",
        "title": "Terminal 2 — Level 2 walking graph (geometry-derived)",
        "disclaimer": "Static hackathon graph: node XY is generated on hub+pier centerlines to match the Level 2 butterfly layout (Level_02_Plan_copia.jpg). Not surveyed GIS data.",
        "plan_reference": "Level_02_Plan_copia.jpg; see also mumbai-terminal-2-map.jpg (T2 overview)",
        "coordinate_system": "normalized_xy_0_100_origin_top_left",
        "units": {"edge_weight": "walk_minutes", "xy": "0-100 normalized to terminal bounding box"},
        "plan_image_transform": {
            "tx_px": -122,
            "ty_px": 18,
            "scale_x": 1.018,
            "scale_y": 0.998,
            "about": "Map UI only: nudge/scales the L02 raster under schematic nodes; tune against Level_02_Plan_copia.jpg.",
        },
        "plan_graph_to_image": {
            "flip_180": True,
            "about": "Map UI: plot at (100-x,100-y) vs JPEG if pier/landside quadrants are inverted.",
        },
    }

    def add_node(nid: str, **kw):
        nodes[nid] = kw

    def add_edge(a: str, b: str):
        ax, ay = nodes[a]["x"], nodes[a]["y"]
        bx, by = nodes[b]["x"], nodes[b]["y"]
        edges.append([a, b, minutes_for((ax, ay), (bx, by))])

    # --- Landside vertical spine (south → security → hub) ---
    add_node(
        "t2_entrance",
        name="Level 2 — Main public entry (south)",
        kind="entrance",
        zone="south_entry",
        terminal="T2",
        floor="L02",
        x=ENTRANCE[0],
        y=ENTRANCE[1],
        accessibility_note="Step-free to security (mock).",
    )
    add_node(
        "t2_circ_south_1",
        name="South circulation — segment 1",
        kind="corridor",
        zone="south_entry",
        terminal="T2",
        floor="L02",
        x=50.0,
        y=82.0,
    )
    add_node(
        "t2_baggage_claim",
        name="Baggage reclaim / arrivals interface (mock)",
        kind="baggage",
        zone="south_entry",
        terminal="T2",
        floor="L02",
        x=BAGGAGE[0],
        y=BAGGAGE[1],
    )
    add_node(
        "t2_circ_south_2",
        name="South circulation — segment 2",
        kind="corridor",
        zone="south_entry",
        terminal="T2",
        floor="L02",
        x=50.0,
        y=72.0,
    )
    add_node(
        "t2_security_intl",
        name="Security — International departures",
        kind="security",
        zone="security_band",
        terminal="T2",
        floor="L02",
        x=SEC_INTL[0],
        y=SEC_INTL[1],
        accessibility_note="Assistance lane (mock).",
    )
    add_node(
        "t2_security_dom",
        name="Security — Domestic departures",
        kind="security",
        zone="security_band",
        terminal="T2",
        floor="L02",
        x=SEC_DOM[0],
        y=SEC_DOM[1],
        accessibility_note="Assistance lane (mock).",
    )
    add_node(
        "t2_security_merge",
        name="Security — merge to airside corridor",
        kind="security",
        zone="security_band",
        terminal="T2",
        floor="L02",
        x=SEC_MERGE[0],
        y=SEC_MERGE[1],
    )
    add_node(
        "t2_post_security",
        name="Airside transition — post security",
        kind="corridor",
        zone="security_band",
        terminal="T2",
        floor="L02",
        x=POST_SEC[0],
        y=POST_SEC[1],
    )

    chain_s = [
        "t2_entrance",
        "t2_circ_south_1",
        "t2_baggage_claim",
        "t2_circ_south_2",
        "t2_security_intl",
        "t2_security_merge",
    ]
    for a, b in zip(chain_s, chain_s[1:]):
        add_edge(a, b)
    add_edge("t2_security_dom", "t2_security_merge")
    add_edge("t2_security_merge", "t2_post_security")

    # --- Hub grid (orthogonal mall spine, on-plan central mass) ---
    hub_ids = []
    for iy, y in enumerate([44.0, 47.0, 50.0, 53.0]):
        row = []
        for ix, x in enumerate([46.0, 48.0, 50.0, 52.0, 54.0]):
            nid = f"t2_hub_{ix:02d}_{iy:02d}"
            row.append(nid)
            add_node(
                nid,
                name=f"Central concourse grid ({ix},{iy})",
                kind="corridor",
                zone="central_mall",
                terminal="T2",
                floor="L02",
                x=x,
                y=y,
            )
        hub_ids.append(row)

    # Connect hub grid orthogonally
    for iy, row in enumerate(hub_ids):
        for ix, nid in enumerate(row):
            if ix + 1 < len(row):
                add_edge(nid, row[ix + 1])
            if iy + 1 < len(hub_ids):
                add_edge(nid, hub_ids[iy + 1][ix])

    # Post-security into hub south row (center)
    add_edge("t2_post_security", "t2_hub_02_03")  # (48,53) close to (50,58)

    # Services / POIs (slight offsets from hub center cells — still visually inside hub)
    svc = [
        ("t2_information", "Information & customer service", "service", 45.0, 45.5),
        ("t2_medical", "Medical station", "service", 55.0, 45.5),
        ("t2_lost_found", "Lost & found", "service", 44.0, 51.0),
        ("t2_forex", "Currency exchange", "service", 56.0, 51.0),
        ("t2_wc_central", "Restrooms — central cluster", "restroom", 47.5, 43.5),
        ("t2_vertical_core", "Lifts / escalators — other levels", "vertical", 50.0, 54.5),
    ]
    for nid, name, kind, x, y in svc:
        add_node(
            nid,
            name=name,
            kind=kind,
            zone="central_mall",
            terminal="T2",
            floor="L02",
            x=x,
            y=y,
            accessibility_note="Step-free access (mock).",
        )
        # snap to nearest hub node
        nearest = min((n for row in hub_ids for n in row), key=lambda hn: dist((x, y), (nodes[hn]["x"], nodes[hn]["y"])))
        add_edge(nearest, nid)

    # --- Four pier spines (strictly collinear hub junction → tip) ---
    pier_specs = [
        ("t2_nw", "pier_nw", "North-West", J_NW, TIP_NW),
        ("t2_ne", "pier_ne", "North-East", J_NE, TIP_NE),
        ("t2_sw", "pier_sw", "South-West", J_SW, TIP_SW),
        ("t2_se", "pier_se", "South-East", J_SE, TIP_SE),
    ]
    spine_start_ids = {}
    for prefix, zone, label, junc, tip in pier_specs:
        sn, ids = spine_nodes(prefix, label, zone, junc, tip, 14)
        for k, v in sn.items():
            # drop internal _label if present
            v.pop("_label", None)
            nodes[k] = v
        spine_start_ids[zone] = ids[0]
        for a, b in zip(ids, ids[1:]):
            add_edge(a, b)
        # attach pier spine start to nearest hub boundary node
        nearest = min((n for row in hub_ids for n in row), key=lambda hn: dist((junc[0], junc[1]), (nodes[hn]["x"], nodes[hn]["y"])))
        add_edge(nearest, ids[0])

    # --- Branch POIs along each pier (WC / F&B / retail) snapped to mid-spine ---
    branches = [
        ("t2_nw", "pier_nw", "t2_nw_wc", "Restrooms — NW pier", "restroom", 6),
        ("t2_nw", "pier_nw", "t2_nw_fb", "F&B — NW pier", "food", 9),
        ("t2_nw", "pier_nw", "t2_nw_retail", "Retail — NW pier", "shopping", 11),
        ("t2_ne", "pier_ne", "t2_ne_wc", "Restrooms — NE pier", "restroom", 5),
        ("t2_ne", "pier_ne", "t2_ne_dutyfree", "Duty-free — NE pier", "shopping", 8),
        ("t2_ne", "pier_ne", "t2_ne_fb", "F&B — NE pier", "food", 10),
        ("t2_sw", "pier_sw", "t2_sw_wc", "Restrooms — SW pier", "restroom", 6),
        ("t2_sw", "pier_sw", "t2_sw_fb", "F&B — SW pier", "food", 9),
        ("t2_sw", "pier_sw", "t2_sw_retail", "Retail — SW pier", "shopping", 12),
        ("t2_se", "pier_se", "t2_se_wc", "Restrooms — SE pier", "restroom", 5),
        ("t2_se", "pier_se", "t2_se_retail", "Retail — SE pier", "shopping", 8),
        ("t2_se", "pier_se", "t2_se_fb", "F&B — SE pier", "food", 11),
    ]
    tips_map = {"t2_nw": TIP_NW, "t2_ne": TIP_NE, "t2_sw": TIP_SW, "t2_se": TIP_SE}
    for prefix, zone, nid, name, kind, spine_i in branches:
        spine_id = f"{prefix}_sp_{spine_i:02d}"
        if spine_id not in nodes:
            spine_id = f"{prefix}_sp_{min(spine_i, 14):02d}"
        base = (nodes[spine_id]["x"], nodes[spine_id]["y"])
        tip = tips_map[prefix]
        off = offset_point(base, tip, 2.2)
        add_node(
            nid,
            name=name,
            kind=kind,
            zone=zone,
            terminal="T2",
            floor="L02",
            x=round(off[0], 2),
            y=round(off[1], 2),
        )
        add_edge(spine_id, nid)

    # Cross-pier optional shortcut through hub only (already connected)

    bundle = {"meta": meta, "nodes": nodes, "edges": edges}
    OUT.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} with {len(nodes)} nodes and {len(edges)} edges.")


if __name__ == "__main__":
    main()
