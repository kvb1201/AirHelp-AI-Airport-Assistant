"""Load static airport graph JSON (nodes + edges)."""

from __future__ import annotations

import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_DEFAULT_GRAPH = _DATA_DIR / "mumbai_t2_level02_graph.json"


def load_graph_bundle(path: str | None = None) -> tuple[dict, list[tuple[str, str, int]], dict]:
    """
    Returns (nodes_dict, edges_list, meta).
    edges_list items: (from_id, to_id, minutes_int).

    Not cached: map meta (plan_image_transform, plan_graph_to_image) must update when JSON changes
    without restarting the API process.
    """
    p = Path(path) if path else _DEFAULT_GRAPH
    raw = json.loads(p.read_text(encoding="utf-8"))
    meta = raw.get("meta", {})
    nodes = raw["nodes"]
    edges: list[tuple[str, str, int]] = []
    for row in raw["edges"]:
        a, b, minutes = row[0], row[1], int(row[2])
        edges.append((a, b, minutes))
    return nodes, edges, meta
