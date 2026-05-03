"""
Graph-based navigation: resolve semantic labels → shortest path (minutes).
Mumbai T2 Level 02 mock graph (see app/data/mumbai_t2_level02_graph.json).
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.core.graph.airport_data import NODES
from app.core.graph.graph_builder import build_airport_graph
from app.core.graph.path_finder import PathFinder


@lru_cache(maxsize=1)
def _finder() -> PathFinder:
    return PathFinder(build_airport_graph())


_LEGACY_GATE: dict[str, str] = {
    "gate_a1": "t2_gate_nw",
    "gate_a2": "t2_gate_nw",
    "gate_b3": "t2_gate_sw",
    "gate_b12": "t2_gate_se",
}

_START_ALIASES: dict[str, str] = {
    # Generic / legacy → T2 L02 nodes
    "entrance": "t2_entrance",
    "entrance_main": "t2_entrance",
    "main_entrance": "t2_entrance",
    "entry": "t2_entrance",
    "unknown": "t2_entrance",
    "checkin": "t2_hub_central",
    "checkin_a": "t2_hub_central",
    "baggage": "t2_baggage_claim",
    "baggage_drop": "t2_baggage_claim",
    "security": "t2_security_intl",
    "security_north": "t2_security_intl",
    "corridor": "t2_hub_central",
    "corridor_t1": "t2_hub_central",
    "food": "t2_fb_nw",
    "food_court": "t2_fb_nw",
    "duty": "t2_duty_ne",
    "duty_free": "t2_duty_ne",
    # T2 explicit aliases
    "hub": "t2_hub_central",
    "central": "t2_hub_central",
    "mall": "t2_hub_central",
    "info": "t2_information",
    "medical": "t2_medical",
    "wc": "t2_wc_central",
    "toilet": "t2_wc_central",
    "restroom": "t2_wc_central",
    "lifts": "t2_vertical_core",
    "elevator": "t2_vertical_core",
    "escalator": "t2_vertical_core",
}


def _normalize_key(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"[\s\-]+", "_", s)
    return s.strip("_")


def resolve_node_id(label: str | None, *, role: str) -> tuple[str | None, str | None]:
    if not label:
        return None, f"missing_{role}"

    key = _normalize_key(label)
    if key in NODES:
        return key, None

    if key in _START_ALIASES:
        return _START_ALIASES[key], None

    if key in _LEGACY_GATE:
        return _LEGACY_GATE[key], None

    return None, f"unknown_{role}"


def extract_goal_node_hint(message: str) -> str | None:
    """
    Resolve goal: explicit t2_* id, pier hints, or legacy gate_a1 style.
    """
    if not message:
        return None
    text = message.lower()

    m = re.search(r"\bt2_[a-z0-9_]+\b", text)
    if m:
        gid = m.group(0)
        if gid in NODES:
            return gid

    if "north west" in text or "northwest" in text or "nw pier" in text:
        return "t2_gate_nw"
    if "north east" in text or "northeast" in text or "ne pier" in text:
        return "t2_gate_ne"
    if "south west" in text or "southwest" in text or "sw pier" in text:
        return "t2_gate_sw"
    if "south east" in text or "southeast" in text or "se pier" in text:
        return "t2_gate_se"

    m = re.search(r"\b(?:gate|boarding)\s*([ab]?)\s*(\d{1,2})\b", text)
    if m:
        letter = (m.group(1) or "a").lower()
        num = int(m.group(2))
        legacy = f"gate_{letter}{num}"
        if legacy in _LEGACY_GATE:
            return _LEGACY_GATE[legacy]

    m = re.search(r"\b([ab])\s*(\d{1,2})\b", text)
    if m:
        legacy = f"gate_{m.group(1)}{int(m.group(2))}"
        if legacy in _LEGACY_GATE:
            return _LEGACY_GATE[legacy]

    return None


def build_route_payload(
    start_id: str,
    goal_id: str,
    *,
    rag_hints: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    _ = rag_hints
    result = _finder().find_path(start_id, goal_id)
    if not result.get("ok"):
        return {
            "ok": False,
            "error": result.get("error", "path_error"),
            "start_id": start_id,
            "goal_id": goal_id,
        }

    node_ids: list[str] = result["node_ids"]
    path_nodes: list[dict[str, Any]] = []
    for nid in node_ids:
        meta = NODES[nid]
        pn: dict[str, Any] = {
            "id": nid,
            "name": meta["name"],
            "kind": meta["kind"],
            "terminal": meta.get("terminal"),
            "zone": meta.get("zone"),
            "floor": meta.get("floor"),
        }
        if "x" in meta and "y" in meta:
            pn["x"] = meta["x"]
            pn["y"] = meta["y"]
        if meta.get("accessibility_note"):
            pn["accessibility_note"] = meta["accessibility_note"]
        path_nodes.append(pn)

    steps: list[str] = []
    for edge in result["edges"]:
        u = NODES[edge["from"]]["name"]
        v = NODES[edge["to"]]["name"]
        minutes = edge["minutes"]
        steps.append(f"{u} → {v} (~{minutes} min walk)")

    return {
        "ok": True,
        "start_id": start_id,
        "goal_id": goal_id,
        "path": path_nodes,
        "edges": result["edges"],
        "total_time_minutes": result["total_minutes"],
        "steps": steps,
    }


def get_route(
    start_label: str,
    goal_label: str,
    *,
    rag_hints: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    start_id, err_s = resolve_node_id(start_label, role="start")
    goal_id, err_g = resolve_node_id(goal_label, role="goal")

    if err_s:
        return {"ok": False, "error": err_s, "hint": "Pick a valid start (e.g. entrance or t2_entrance)."}
    if err_g:
        return {
            "ok": False,
            "error": err_g,
            "hint": "Pick a destination node (e.g. t2_gate_ne or NE pier gate).",
        }

    return build_route_payload(start_id, goal_id, rag_hints=rag_hints)


def plan_navigation_from_chat(
    *,
    user_message: str,
    location_label: str | None,
    destination_label: str | None = None,
    rag_snippets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    start = location_label or "t2_entrance"
    goal = destination_label or extract_goal_node_hint(user_message)

    if not goal:
        return {
            "ok": False,
            "error": "goal_required",
            "hint": "Say a pier (NE/NW/SE/SW gate), or a node id like t2_gate_ne.",
        }

    return get_route(start, goal, rag_hints=rag_snippets)
