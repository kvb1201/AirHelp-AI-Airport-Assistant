"""
Map RAG / LLM airport_data navigation node ids → Mumbai T2 L02 walking graph ids.

- Does **not** modify ``airport_data.json`` or ``mumbai_t2_level02_graph.json``.
- Optional overrides live in ``app/data/rag_to_graph_node_map.json`` (extend only that file).
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_MAP_PATH = _DATA_DIR / "rag_to_graph_node_map.json"


def _normalize_key(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"[\s\-]+", "_", s)
    return s.strip("_")


@lru_cache(maxsize=1)
def _graph_ids() -> frozenset[str]:
    from app.core.graph.airport_data import NODES

    return frozenset(NODES.keys())


@lru_cache(maxsize=1)
def _manual_rag_to_graph() -> dict[str, str]:
    if not _MAP_PATH.exists():
        return {}
    try:
        data = json.loads(_MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    raw = data.get("rag_to_graph")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in raw.items():
        if not k or not isinstance(k, str):
            continue
        if not v or not isinstance(v, str):
            continue
        ks, vs = k.strip(), v.strip()
        if ks and vs:
            out[ks] = vs
    return out


def _legacy_gate_graph_id(normalized_body: str) -> str | None:
    """Reuse pier-tip resolution from navigation_service without import cycles at load time."""
    from app.services.navigation_service import _LEGACY_GATE

    if normalized_body in _LEGACY_GATE:
        return _LEGACY_GATE[normalized_body]
    return None


def resolve_to_graph_node_id(candidate: str | None) -> tuple[str | None, str]:
    """
    Resolve a user/RAG id to a graph node id present in ``mumbai_t2_level02_graph.json``.

    Returns:
        (graph_node_id or None, reason tag): ``graph_exact`` | ``graph_normalized`` |
        ``manual_map`` | ``heuristic_node_prefix`` | ``legacy_gate`` | ``empty`` | ``unmapped`` |
        ``manual_bad_target``
    """
    if not candidate or not str(candidate).strip():
        return None, "empty"

    raw = str(candidate).strip()
    gids = _graph_ids()

    if raw in gids:
        return raw, "graph_exact"

    nk = _normalize_key(raw)
    if nk in gids:
        return nk, "graph_normalized"

    manual = _manual_rag_to_graph()
    if raw in manual:
        tid = manual[raw]
        return (tid, "manual_map") if tid in gids else (None, "manual_bad_target")
    if nk in manual:
        tid = manual[nk]
        return (tid, "manual_map") if tid in gids else (None, "manual_bad_target")

    rlow = raw.lower()
    if rlow.startswith("node-"):
        body = raw[5:]
        nb = _normalize_key(body)
        if nb in gids:
            return nb, "heuristic_node_prefix"
        leg = _legacy_gate_graph_id(nb)
        if leg and leg in gids:
            return leg, "legacy_gate"

    leg = _legacy_gate_graph_id(nk)
    if leg and leg in gids:
        return leg, "legacy_gate"

    return None, "unmapped"


def coerce_to_graph_node_id(candidate: str | None) -> str | None:
    """Return a valid graph id, or None if the value cannot be mapped."""
    gid, _reason = resolve_to_graph_node_id(candidate)
    return gid
