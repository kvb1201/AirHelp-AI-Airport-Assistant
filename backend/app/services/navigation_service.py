"""
Graph-based navigation: resolve semantic labels → shortest path (minutes).
Mumbai T2 Level 02 — dense graph from scripts/build_mumbai_t2_l02_graph.py
"""

from __future__ import annotations

import re
from typing import Any

from app.core.graph.airport_data import EDGES, NODES
from app.core.graph.graph_builder import build_airport_graph
from app.core.graph.path_finder import PathFinder
from app.services import congestion
from app.services.route_narrative import (
    build_simple_journey,
    passenger_place_name,
    shops_along_path,
)


# Pier gate ends (spine segment 14 = approach to gate lounge)
_PIER_TIP = {
    "nw": "t2_nw_sp_14",
    "ne": "t2_ne_sp_14",
    "sw": "t2_sw_sp_14",
    "se": "t2_se_sp_14",
}

_LEGACY_GATE: dict[str, str] = {
    "gate_a1": _PIER_TIP["nw"],
    "gate_a2": _PIER_TIP["nw"],
    "gate_b3": _PIER_TIP["sw"],
    "gate_b12": _PIER_TIP["se"],
    "gate_nw": _PIER_TIP["nw"],
    "gate_ne": _PIER_TIP["ne"],
    "gate_sw": _PIER_TIP["sw"],
    "gate_se": _PIER_TIP["se"],
    "t2_gate_nw": _PIER_TIP["nw"],
    "t2_gate_ne": _PIER_TIP["ne"],
    "t2_gate_sw": _PIER_TIP["sw"],
    "t2_gate_se": _PIER_TIP["se"],
}

_START_ALIASES: dict[str, str] = {
    "entrance": "t2_entrance",
    "entrance_main": "t2_entrance",
    "main_entrance": "t2_entrance",
    "entry": "t2_entrance",
    "unknown": "t2_entrance",
    "baggage": "t2_baggage_claim",
    "baggage_drop": "t2_baggage_claim",
    "security": "t2_security_intl",
    "security_north": "t2_security_intl",
    "security_intl": "t2_security_intl",
    "security_dom": "t2_security_dom",
    "checkin": "t2_hub_02_02",
    "checkin_a": "t2_hub_02_02",
    "hub": "t2_hub_02_02",
    "central": "t2_hub_02_02",
    "mall": "t2_hub_02_02",
    "corridor": "t2_hub_02_02",
    "corridor_t1": "t2_hub_02_02",
    "t2_hub_central": "t2_hub_02_02",
    "info": "t2_information",
    "medical": "t2_medical",
    "wc": "t2_wc_central",
    "toilet": "t2_wc_central",
    "restroom": "t2_wc_central",
    "lifts": "t2_vertical_core",
    "elevator": "t2_vertical_core",
    "escalator": "t2_vertical_core",
    "food": "t2_nw_fb",
    "food_court": "t2_nw_fb",
    "duty": "t2_ne_dutyfree",
    "duty_free": "t2_ne_dutyfree",
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
    if not message:
        return None
    text = message.lower()

    m = re.search(r"\bt2_[a-z0-9_]+\b", text)
    if m:
        gid = m.group(0)
        if gid in NODES:
            return gid

    if "north west" in text or "northwest" in text or "nw pier" in text:
        return _PIER_TIP["nw"]
    if "north east" in text or "northeast" in text or "ne pier" in text:
        return _PIER_TIP["ne"]
    if "south west" in text or "southwest" in text or "sw pier" in text:
        return _PIER_TIP["sw"]
    if "south east" in text or "southeast" in text or "se pier" in text:
        return _PIER_TIP["se"]

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


def _path_nodes_from_ids(node_ids: list[str]) -> list[dict[str, Any]]:
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
    return path_nodes


def _route_option(
    start_id: str,
    goal_id: str,
    *,
    node_ids: list[str],
    edges: list[dict[str, Any]],
    total_minutes: int,
    option_index: int,
    option_label: str,
) -> dict[str, Any]:
    path_nodes = _path_nodes_from_ids(node_ids)
    steps: list[str] = []
    for edge in edges:
        um = dict(NODES[edge["from"]])
        um["id"] = edge["from"]
        vm = dict(NODES[edge["to"]])
        vm["id"] = edge["to"]
        u = passenger_place_name(um)
        v = passenger_place_name(vm)
        minutes = edge["minutes"]
        steps.append(f"{u} → {v} (~{minutes} min walk)")

    journey = build_simple_journey(path_nodes, edges, int(total_minutes))
    shop_along = shops_along_path(node_ids, max_total=10)

    return {
        "option_index": option_index,
        "option_label": option_label,
        "path": path_nodes,
        "edges": edges,
        "total_time_minutes": int(total_minutes),
        "node_count": len(path_nodes),
        "steps": steps,
        "simple_journey": journey,
        "shops_along_route": shop_along,
    }


def build_route_payload(
    start_id: str,
    goal_id: str,
    *,
    rag_hints: list[dict[str, Any]] | None = None,
    local_hour: int | None = None,
    busy_terminal: bool = False,
) -> dict[str, Any]:
    _ = rag_hints
    hour = int(local_hour) if local_hour is not None else congestion.default_terminal_local_hour()
    hour = hour % 24
    extras = congestion.security_extras_for_context(local_hour=hour, busy_terminal=busy_terminal)
    finder = PathFinder(build_airport_graph(security_queue_minutes=float(extras.mid)))

    k_paths = finder.find_k_paths(start_id, goal_id, k=3)
    if not k_paths:
        probe = finder.find_path(start_id, goal_id)
        if not probe.get("ok"):
            return {
                "ok": False,
                "error": probe.get("error", "path_error"),
                "start_id": start_id,
                "goal_id": goal_id,
            }
        k_paths = [probe]

    labels = ["Fastest route", "Alternative 2", "Alternative 3"]
    routes: list[dict[str, Any]] = []
    for i, pr in enumerate(k_paths):
        lab = labels[i] if i < len(labels) else f"Option {i + 1}"
        node_ids = pr["node_ids"]
        low, mid, high, n_sec = congestion.path_time_bands_minutes(
            node_ids,
            edges_base=EDGES,
            nodes=NODES,
            extras=extras,
        )
        total_mid = int(round(mid))
        routes.append(
            _route_option(
                start_id,
                goal_id,
                node_ids=node_ids,
                edges=pr["edges"],
                total_minutes=total_mid,
                option_index=i,
                option_label=lab,
            )
        )
        cb = congestion.congestion_public_block(
            local_hour=hour,
            busy_terminal=busy_terminal,
            extras=extras,
            security_edges_on_route=n_sec,
        )
        routes[-1]["congestion"] = {
            "total_time_minutes_low": int(low),
            "total_time_minutes_mid": total_mid,
            "total_time_minutes_high": int(high),
            **cb,
        }

    primary = routes[0]
    out: dict[str, Any] = {
        "ok": True,
        "start_id": start_id,
        "goal_id": goal_id,
        "route_count": len(routes),
        "routes": routes,
    }
    out.update(primary)
    return out


def get_route(
    start_label: str,
    goal_label: str,
    *,
    rag_hints: list[dict[str, Any]] | None = None,
    local_hour: int | None = None,
    busy_terminal: bool = False,
) -> dict[str, Any]:
    start_id, err_s = resolve_node_id(start_label, role="start")
    goal_id, err_g = resolve_node_id(goal_label, role="goal")

    if err_s:
        return {"ok": False, "error": err_s, "hint": "Pick a valid start (e.g. entrance or t2_entrance)."}
    if err_g:
        return {
            "ok": False,
            "error": err_g,
            "hint": "Pick a destination (pier gate id like t2_ne_sp_14, or say NE pier).",
        }

    return build_route_payload(
        start_id,
        goal_id,
        rag_hints=rag_hints,
        local_hour=local_hour,
        busy_terminal=busy_terminal,
    )


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
            "hint": "Say NE/NW/SE/SW pier gate, or a node id (e.g. t2_ne_sp_14).",
        }

    return get_route(
        start,
        goal,
        rag_hints=rag_snippets,
        local_hour=congestion.default_terminal_local_hour(),
        busy_terminal=False,
    )
