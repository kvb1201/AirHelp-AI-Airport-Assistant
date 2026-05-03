"""
Graph-based navigation: resolve semantic labels → shortest path (minutes).
Mumbai T2 Level 02 — dense graph from scripts/build_mumbai_t2_l02_graph.py
"""

from __future__ import annotations

import re
from typing import Any

from app.core.graph.airport_data import EDGES, NODES
from app.core.graph.node_mapper import resolve_to_graph_node_id
from app.core.graph.graph_builder import build_airport_graph
from app.core.graph.path_finder import PathFinder
from app.services import congestion
from app.services.route_narrative import (
    build_simple_journey,
    passenger_place_name,
    shops_along_path,
)
from app.services.turn_by_turn import (
    generate_summary_stats,
    generate_turn_by_turn_directions,
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

    mapped, _how = resolve_to_graph_node_id(label)
    if mapped:
        return mapped, None

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

    m = re.search(r"\bnode-[a-z0-9]+(?:-[a-z0-9]+)*\b", text, re.I)
    if m:
        rag_id = m.group(0)
        resolved, how = resolve_to_graph_node_id(rag_id)
        if resolved and how != "unmapped":
            return resolved

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


def _alnum_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _match_csv_poi_label(
    label: str | None,
    rows: list[dict[str, object]],
    *,
    start_graph_id: str | None = None,
    avoid_graph_node_id: str | None = None,
) -> str | None:
    """Match ``name_display`` / ``name_normalized`` against ``graph_node_id`` rows (shops or facilities CSV)."""
    if not label or not str(label).strip():
        return None
    raw = str(label).strip().rstrip("?.!\"' ")
    qk = _alnum_key(raw)
    if len(qk) < 2:
        return None

    ranked: list[tuple[int, str]] = []
    for row in rows:
        gid = str(row.get("graph_node_id") or "").strip()
        if not gid or gid not in NODES:
            continue
        disp = str(row.get("name_display", "")).strip().lower()
        norm = str(row.get("name_normalized", "")).strip().lower()
        nk = _alnum_key(norm)
        dk = _alnum_key(disp)
        rlo = raw.lower()

        score = 0
        if qk == nk or qk == dk:
            score = 100
        elif rlo == disp or rlo == norm:
            score = 99
        elif disp and min(len(disp), len(rlo)) >= 4 and (disp in rlo or rlo in disp):
            score = 85
        elif nk and len(qk) >= 4 and (qk in nk or nk in qk):
            score = 75
        elif dk and len(qk) >= 4 and (qk in dk or dk in qk):
            score = 74

        if score:
            ranked.append((score, gid))

    if not ranked:
        return None

    top_s = max(s for s, _ in ranked)
    ties = list(dict.fromkeys(g for s, g in ranked if s == top_s))
    if (
        avoid_graph_node_id
        and avoid_graph_node_id in NODES
        and avoid_graph_node_id in ties
        and len(ties) > 1
    ):
        alt = [t for t in ties if t != avoid_graph_node_id]
        if alt:
            ties = alt
    if len(ties) == 1:
        return ties[0]
    sid = start_graph_id if start_graph_id in NODES else None
    if sid:
        picked = _nearest_graph_node(sid, tuple(ties))
        if picked:
            return picked
    return ties[0]


def resolve_shop_name_to_graph_node(
    label: str | None,
    *,
    start_graph_id: str | None = None,
    avoid_graph_node_id: str | None = None,
) -> str | None:
    """
    Resolve a retail / shop name using ``shops_t2_l02.csv`` (``graph_node_id``).
    ``avoid_graph_node_id`` drops that node from tie-breaks (e.g. goal must differ from start).
    """
    from app.services.shops_loader import load_shops_t2_l02

    return _match_csv_poi_label(
        label,
        load_shops_t2_l02(),
        start_graph_id=start_graph_id,
        avoid_graph_node_id=avoid_graph_node_id,
    )


def resolve_facility_name_to_graph_node(
    label: str | None,
    *,
    start_graph_id: str | None = None,
    avoid_graph_node_id: str | None = None,
) -> str | None:
    """Resolve a facility row from ``facilities_bom.csv`` (e.g. Lost and Found, Wi‑Fi desk)."""
    from app.services.facilities_loader import load_facilities_bom

    return _match_csv_poi_label(
        label,
        load_facilities_bom(),
        start_graph_id=start_graph_id,
        avoid_graph_node_id=avoid_graph_node_id,
    )


def resolve_place_label_to_graph_node(
    label: str | None,
    *,
    disambiguate_nearest_from: str | None = None,
) -> str | None:
    """
    Resolve ``location`` / ``source`` text to a walking-graph node id (same order as goals):
    graph id / ``node-*`` / aliases / gates via ``resolve_node_id``, then shop and facility CSV names.
    """
    if not label or not str(label).strip():
        return None
    s = str(label).strip()
    gid, _ = resolve_node_id(s, role="start")
    if gid:
        return gid
    tie = disambiguate_nearest_from if (disambiguate_nearest_from or "") in NODES else None
    gid = resolve_shop_name_to_graph_node(s, start_graph_id=tie)
    if gid:
        return gid
    return resolve_facility_name_to_graph_node(s, start_graph_id=tie)


# RAG snippets name food/shops but ``airport_data.json`` has no graph node id — map to L02 hubs.
_FOOD_RESULT_CATS = frozenset({"food_court", "restaurant", "cafe", "coffee_shop", "quick_bites"})
_SHOP_RESULT_CATS = frozenset({"shop"})
_FOOD_ZONE_BY_QUAD = {
    "nw": "t2_nw_fb",
    "ne": "t2_ne_fb",
    "sw": "t2_sw_fb",
    "se": "t2_se_fb",
}
_RETAIL_ZONE_BY_QUAD = {
    "nw": "t2_nw_retail",
    "ne": "t2_ne_dutyfree",
    "sw": "t2_sw_retail",
    "se": "t2_se_retail",
}


def _infer_quad_from_blurb(text: str) -> str | None:
    t = (text or "").lower()
    if re.search(r"\b(northwest|north\s*west|nw\s*pier|\bnw\b)", t):
        return "nw"
    if re.search(r"\b(northeast|north\s*east|ne\s*pier|\bne\b)", t):
        return "ne"
    if re.search(r"\b(southwest|south\s*west|sw\s*pier|\bsw\b)", t):
        return "sw"
    if re.search(r"\b(southeast|south\s*east|se\s*pier|\bse\b)", t):
        return "se"
    return None


def _nearest_graph_node(start_id: str, candidates: tuple[str, ...]) -> str | None:
    if start_id not in NODES:
        return candidates[0] if candidates else None
    g = build_airport_graph(0.0)
    pf = PathFinder(g)
    best: str | None = None
    best_t = 1e12
    for c in candidates:
        if c not in g:
            continue
        p = pf.find_path(start_id, c)
        if p.get("ok"):
            tm = float(p.get("total_minutes", 1e12))
            if tm < best_t:
                best_t = tm
                best = c
    return best


def goal_from_rag_snippets(
    snippets: list[dict[str, Any]],
    start_graph_id: str,
) -> str | None:
    """
    When the user names a venue from RAG (outlet name, no ``t2_*`` id), pick a routable graph node:
    quadrant hint from snippet text if present, otherwise the food / retail hub closest to ``start``.
    """
    if not snippets:
        return None
    sid = start_graph_id if start_graph_id in NODES else None
    if not sid:
        sid, _ = resolve_node_id("t2_entrance", role="start")
    if not sid:
        return None

    for sn in snippets[:10]:
        cat = (sn.get("category") or "").lower()
        blob = f"{sn.get('name', '')} {sn.get('description', '')} {sn.get('location', '')}"
        quad = _infer_quad_from_blurb(blob)
        if cat in _FOOD_RESULT_CATS:
            if quad:
                return _FOOD_ZONE_BY_QUAD[quad]
            n = _nearest_graph_node(sid, tuple(_FOOD_ZONE_BY_QUAD.values()))
            if n:
                return n
        if cat in _SHOP_RESULT_CATS:
            if quad:
                return _RETAIL_ZONE_BY_QUAD[quad]
            n = _nearest_graph_node(sid, tuple(_RETAIL_ZONE_BY_QUAD.values()))
            if n:
                return n
    return None


def resolve_walking_goal_id(
    *,
    user_message: str,
    destination_label: str | None,
    rag_snippets: list[dict[str, Any]] | None,
    start_graph_id: str,
) -> str | None:
    """Resolve user text + optional RAG rows to a single graph node id for routing."""
    tried: list[str] = []
    h = extract_goal_node_hint(user_message)
    if h:
        tried.append(h)
    if destination_label and str(destination_label).strip():
        d = str(destination_label).strip()
        if d not in tried:
            tried.append(d)
    tail_m = re.search(
        r"(?:take\s+me\s+to|navigate\s+to|walk\s+me\s+to|guide\s+me\s+to|want\s+to\s+go\s+to|going\s+to|need\s+to\s+(?:get\s+to|go\s+to)|(?:get|bring|lead)\s+me\s+to)\s+(.+?)\s*$",
        user_message.strip(),
        re.I | re.S,
    )
    if tail_m:
        tail = tail_m.group(1).strip().strip("\"'").rstrip("?.! ")
        if tail and tail not in tried:
            tried.append(tail)
    for lab in tried:
        gid, _ = resolve_node_id(lab, role="goal")
        if gid:
            return gid

    sid = start_graph_id if start_graph_id in NODES else None
    if not sid:
        sid, _ = resolve_node_id("t2_entrance", role="start")

    for lab in tried:
        sg = resolve_shop_name_to_graph_node(
            lab, start_graph_id=sid, avoid_graph_node_id=sid
        )
        if sg:
            return sg
        fg = resolve_facility_name_to_graph_node(
            lab, start_graph_id=sid, avoid_graph_node_id=sid
        )
        if fg:
            return fg

    if rag_snippets and sid:
        g = goal_from_rag_snippets(rag_snippets, sid)
        if g:
            return g
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
    
    # Generate detailed turn-by-turn directions
    turn_by_turn = generate_turn_by_turn_directions(path_nodes, edges)
    summary_stats = generate_summary_stats(turn_by_turn)

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
        "turn_by_turn_directions": turn_by_turn,
        "route_summary": summary_stats,
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
    start_raw = (location_label or "").strip() or "t2_entrance"
    start_id = resolve_place_label_to_graph_node(start_raw)
    if not start_id:
        start_id, _ = resolve_node_id(start_raw, role="start")
    if not start_id:
        start_id, _ = resolve_node_id("t2_entrance", role="start")

    goal = resolve_walking_goal_id(
        user_message=user_message,
        destination_label=destination_label,
        rag_snippets=rag_snippets,
        start_graph_id=start_id or "t2_entrance",
    )

    if not goal:
        return {
            "ok": False,
            "error": "goal_required",
            "hint": "Say NE/NW/SE/SW pier gate, a node id (e.g. t2_ne_sp_14), or pick a food/shop from suggestions then navigate.",
        }

    return get_route(
        start_id,
        goal,
        rag_hints=rag_snippets,
        local_hour=congestion.default_terminal_local_hour(),
        busy_terminal=False,
    )
