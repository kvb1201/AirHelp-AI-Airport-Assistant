"""Guided walking: checkpoint questions along a path + relocalization from user-reported landmarks."""

from __future__ import annotations

import re
from typing import Any

import networkx as nx

from app.core.graph.airport_data import NODES
from app.core.graph.graph_builder import build_airport_graph
from app.services import congestion
from app.services.facilities_loader import load_facilities_bom
from app.services.route_narrative import passenger_place_name
from app.services.shops_loader import load_shops_t2_l02


def _graph_for_query(*, local_hour: int | None, busy_terminal: bool) -> nx.Graph:
    hour = int(local_hour) if local_hour is not None else congestion.default_terminal_local_hour()
    hour %= 24
    extras = congestion.security_extras_for_context(local_hour=hour, busy_terminal=busy_terminal)
    return build_airport_graph(security_queue_minutes=float(extras.mid))


def _node_dict(node_id: str) -> dict[str, Any]:
    meta = NODES[node_id]
    d: dict[str, Any] = {**meta}
    d["id"] = node_id
    return d


def _compress_waypoint_indices(path_len: int, max_steps: int = 14) -> list[int]:
    """Indices into path_node_ids: always include 0 and path_len-1; subsample long paths."""
    if path_len <= 0:
        return []
    if path_len == 1:
        return [0]
    if path_len <= max_steps:
        return list(range(path_len))
    cap = max_steps
    interior_budget = max(1, cap - 2)
    out = [0]
    for k in range(1, interior_budget + 1):
        idx = round(k * (path_len - 1) / (interior_budget + 1))
        idx = max(1, min(path_len - 2, idx))
        if idx > out[-1]:
            out.append(idx)
    if out[-1] != path_len - 1:
        out.append(path_len - 1)
    return sorted(set(out))


def _segment_minutes(path: list[str], edges: list[dict[str, Any]], i_from: int, i_to: int) -> int:
    if i_to <= i_from:
        return 0
    total = 0
    for j in range(i_from, i_to):
        u, v = path[j], path[j + 1]
        found = False
        for e in edges:
            if e.get("from") == u and e.get("to") == v:
                total += int(e.get("minutes", 0))
                found = True
                break
        if not found:
            for e in edges:
                if (e.get("from") == u and e.get("to") == v) or (e.get("from") == v and e.get("to") == u):
                    total += int(e.get("minutes", 0))
                    found = True
                    break
            if not found:
                total += 2
    return total


def _landmarks_at_node(node_id: str) -> tuple[list[str], list[str]]:
    fac_names: list[str] = []
    shop_names: list[str] = []
    for f in load_facilities_bom():
        if str(f.get("graph_node_id") or "").strip() != node_id:
            continue
        name = str(f.get("name_display") or "").strip()
        if name and name not in fac_names:
            fac_names.append(name)
    for s in load_shops_t2_l02():
        if str(s.get("graph_node_id") or "").strip() != node_id:
            continue
        name = str(s.get("name_display") or "").strip()
        if name and name not in shop_names:
            shop_names.append(name)
    return fac_names[:5], shop_names[:5]


def build_guided_checkpoints(
    path: list[str],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    if not path or len(path) < 2:
        return {"ok": False, "error": "path_too_short", "hint": "Need at least two nodes for guidance."}
    for nid in path:
        if nid not in NODES:
            return {"ok": False, "error": "unknown_node", "node_id": nid}

    wp = _compress_waypoint_indices(len(path))
    steps: list[dict[str, Any]] = []
    for s in range(len(wp) - 1):
        i0, i1 = wp[s], wp[s + 1]
        u_id, v_id = path[i0], path[i1]
        walk_m = _segment_minutes(path, edges, i0, i1)
        fac, shops = _landmarks_at_node(v_id)
        look = fac + shops
        if not look:
            meta_v = _node_dict(v_id)
            look = [passenger_place_name(meta_v)]
        to_label = passenger_place_name(_node_dict(v_id))
        from_label = passenger_place_name(_node_dict(u_id))
        q_parts = [f"From {from_label}, walk about {walk_m} minutes toward {to_label}."]
        if look:
            preview = ", ".join(look[:4])
            q_parts.append(f"When you arrive, look for: {preview}.")
        q_parts.append("Do you see these cues (or this area)?")
        steps.append(
            {
                "step_index": s,
                "from_path_index": i0,
                "to_path_index": i1,
                "from_node_id": u_id,
                "to_node_id": v_id,
                "walk_minutes": walk_m,
                "from_place_label": from_label,
                "to_place_label": to_label,
                "look_for": look[:8],
                "facilities": fac,
                "shops": shops,
                "question": " ".join(q_parts),
            }
        )

    return {
        "ok": True,
        "path": path,
        "waypoint_path_indices": wp,
        "step_count": len(steps),
        "steps": steps,
    }


_SYNONYM_GROUPS: list[tuple[str, list[str]]] = [
    ("restroom", ["washroom", "toilet", "restroom", "wc", "bathroom", "loo", "urinal"]),
    ("coffee", ["coffee", "cafe", "café", "starbucks", "barista"]),
    ("food", ["food", "restaurant", "meal", "dining", "burger", "pizza", "kitchen"]),
    ("duty", ["duty", "dutyfree", "duty-free", "cosmetics", "liquor"]),
    ("information", ["information", "info", "help", "desk", "counter"]),
    ("medical", ["medical", "doctor", "pharmacy", "clinic"]),
    ("baggage", ["baggage", "luggage", "belt", "carousel", "reclaim"]),
    ("security", ["security", "screening", "checkpoint"]),
    ("entrance", ["entrance", "entry", "door", "curb"]),
]


def _expand_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for _, syns in _SYNONYM_GROUPS:
        for t in list(expanded):
            if t in syns:
                expanded.update(syns)
    return expanded


def _text_match_score(hay: str, expanded: set[str]) -> int:
    h = hay.lower()
    score = 0
    for t in expanded:
        if len(t) < 2:
            continue
        if t in h:
            score += 5 if len(t) > 3 else 2
    return score


def _poi_candidates_from_observation(observation: str) -> list[tuple[str, str, int]]:
    """Return (graph_node_id, label, match_score) sorted by score."""
    tokens = set(re.findall(r"[a-zà-ÿ0-9]+", observation.lower()))
    if not tokens:
        return []
    expanded = _expand_tokens(tokens)
    best: dict[str, tuple[str, int]] = {}

    def consider(nid: str, label: str, sc: int) -> None:
        if not nid or nid not in NODES:
            return
        old = best.get(nid)
        if old is None or sc > old[1]:
            best[nid] = (label, sc)

    for f in load_facilities_bom():
        gid = str(f.get("graph_node_id") or "").strip()
        blob = " ".join(
            [
                str(f.get("name_display") or ""),
                str(f.get("name_normalized") or ""),
                str(f.get("category") or ""),
                str(f.get("listing_location") or ""),
            ]
        )
        sc = _text_match_score(blob, expanded)
        if sc > 0:
            consider(gid, str(f.get("name_display") or gid), sc)

    for s in load_shops_t2_l02():
        gid = str(s.get("graph_node_id") or "").strip()
        blob = " ".join([str(s.get("name_display") or ""), str(s.get("category") or "")])
        sc = _text_match_score(blob, expanded)
        if sc > 0:
            consider(gid, str(s.get("name_display") or gid), sc)

    for nid, meta in NODES.items():
        kind = str(meta.get("kind") or "")
        name = str(meta.get("name") or "")
        blob = f"{nid} {kind} {name}"
        sc_node = _text_match_score(blob, expanded)
        if any(t in expanded for t in ("washroom", "toilet", "restroom", "wc", "bathroom", "loo")):
            if "wc" in nid or kind == "restroom":
                sc_node += 8
        if sc_node > 0:
            consider(nid, passenger_place_name(_node_dict(nid)), sc_node)

    out = [(nid, lab, sc) for nid, (lab, sc) in best.items()]
    out.sort(key=lambda x: -x[2])
    return out


def _min_walk_minutes(G: nx.Graph, sources: list[str], target: str) -> int | None:
    best: int | None = None
    for s in sources:
        if s not in G or target not in G:
            continue
        if not nx.has_path(G, s, target):
            continue
        d = int(round(nx.shortest_path_length(G, s, target, weight="minutes")))
        if best is None or d < best:
            best = d
    return best


def relocalize(
    *,
    path: list[str],
    last_confirmed_path_index: int,
    next_waypoint_path_index: int,
    observation: str,
    local_hour: int | None = None,
    busy_terminal: bool = False,
    max_results: int = 5,
) -> dict[str, Any]:
    if not path:
        return {"ok": False, "error": "missing_path"}
    obs = (observation or "").strip()
    if not obs:
        return {"ok": False, "error": "missing_observation", "hint": "Describe what you see nearby."}

    G = _graph_for_query(local_hour=local_hour, busy_terminal=busy_terminal)
    lo = max(0, last_confirmed_path_index - 1)
    hi = min(len(path), next_waypoint_path_index + 2)
    anchor_nodes = list(dict.fromkeys(path[lo:hi]))

    pois = _poi_candidates_from_observation(obs)
    if not pois:
        return {
            "ok": True,
            "matched": False,
            "hint": "Try naming something from the map: restroom, coffee, security, information desk, baggage…",
            "candidates": [],
        }

    lc = max(0, min(last_confirmed_path_index, len(path) - 1))
    anchor_focus = path[lc]

    ranked_raw: list[tuple[dict[str, Any], float]] = []
    for nid, label, match_sc in pois[:50]:
        if nid not in G:
            continue
        dist_band = _min_walk_minutes(G, anchor_nodes, nid)
        dist_focus = _min_walk_minutes(G, [anchor_focus], nid)
        dist_primary = dist_focus if dist_focus is not None else dist_band
        if dist_primary is None:
            continue
        rank_score = float(match_sc) * 12.0 - float(dist_primary)
        row = {
            "graph_node_id": nid,
            "label": label,
            "walking_minutes_from_last_anchor": dist_primary,
            "walking_minutes_from_route_band": dist_band,
            "match_score": match_sc,
            "note": f"About {dist_primary} min walk from your last confirmed spot on the route.",
        }
        ranked_raw.append((row, rank_score))

    ranked_raw.sort(key=lambda x: -x[1])
    out: list[dict[str, Any]] = []
    seen_id: set[str] = set()
    for r, _ in ranked_raw:
        gid = r["graph_node_id"]
        if gid in seen_id:
            continue
        seen_id.add(gid)
        out.append(r)
        if len(out) >= max_results:
            break

    return {
        "ok": True,
        "matched": True,
        "candidates": out,
        "hint": "Pick the place closest to what you see. We will replan walking directions from that spot.",
    }
