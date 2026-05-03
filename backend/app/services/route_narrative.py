"""
Human-readable walking directions + shop/dine picks along a computed graph path.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.shops_loader import load_shops_t2_l02

_PIER_WORD = {
    "nw": "North-west",
    "ne": "North-east",
    "sw": "South-west",
    "se": "South-east",
}


def passenger_place_name(node: dict[str, Any]) -> str:
    """
    Short, plain-language label for maps and walking tips.
    Avoids internal spine segment numbers (e.g. 'segment 7/14').
    """
    nid = str(node.get("id") or "")
    kind = str(node.get("kind") or "")

    if nid == "t2_entrance":
        return "Main entrance"
    if nid == "t2_baggage_claim":
        return "Baggage reclaim area"
    if nid in ("t2_security_intl", "t2_security_dom", "t2_security_merge"):
        return "Security"
    if nid == "t2_post_security":
        return "After security (airside)"
    if nid == "t2_vertical_core":
        return "Lifts & escalators (other floors)"
    if nid == "t2_l03_postsec":
        return "Level 3 — shops & dining (after security)"
    if nid == "t2_l04_postsec":
        return "Level 4 — shops & dining (after security)"
    if nid == "bom_t1_retail_hub":
        return "Terminal 1 side (other building)"
    if nid == "t2_information":
        return "Information desk"
    if nid == "t2_lost_found":
        return "Lost & found"
    if nid == "t2_medical":
        return "Medical / special assistance"
    if nid == "t2_forex":
        return "Money change / ATMs area"
    if nid == "t2_wc_central":
        return "Restrooms (central)"
    if nid.startswith("t2_nw_fb") or nid == "t2_nw_fb":
        return "Food & drink (north-west side)"
    if nid.startswith("t2_ne_fb") or nid == "t2_ne_fb":
        return "Food & drink (north-east side)"
    if nid.startswith("t2_sw_fb") or nid == "t2_sw_fb":
        return "Food & drink (south-west side)"
    if nid.startswith("t2_se_fb") or nid == "t2_se_fb":
        return "Food & drink (south-east side)"
    if nid.startswith("t2_ne_dutyfree") or nid == "t2_ne_dutyfree":
        return "Duty-free shopping (north-east)"
    if nid.startswith("t2_nw_retail") or nid == "t2_nw_retail":
        return "Shops (north-west pier)"
    if nid.startswith("t2_sw_retail") or nid == "t2_sw_retail":
        return "Shops (south-west pier)"
    if nid.startswith("t2_se_retail") or nid == "t2_se_retail":
        return "Shops (south-east pier)"

    m = re.match(r"t2_(nw|ne|sw|se)_sp_(\d+)$", nid)
    if m:
        pier, seg_s = m.group(1), m.group(2)
        label = _PIER_WORD.get(pier, pier.upper())
        seg = int(seg_s)
        if seg >= 12:
            return f"{label} pier — near the gate area"
        if seg >= 6:
            return f"{label} pier — along the boarding walk"
        if seg >= 1:
            return f"{label} pier — from the main hall toward the gates"
        return f"{label} pier — start of the boarding walk"

    hm = re.match(r"t2_hub_(\d+)_(\d+)$", nid)
    if hm:
        col, row = int(hm.group(1)), int(hm.group(2))
        ew = "middle of the main hall"
        if col <= 1:
            ew = "west side of the main hall"
        elif col >= 3:
            ew = "east side of the main hall"
        ns = "centre"
        if row <= 1:
            ns = "toward security / arrivals side"
        elif row >= 3:
            ns = "toward the piers / gates side"
        return f"Main hall — {ew}, {ns}"
    if nid.startswith("t2_circ_south"):
        return "Walkway near the entrance"
    if kind == "gate" and "Gate lounge" in str(node.get("name") or ""):
        return "Gate lounge area"

    name = str(node.get("name") or "")
    name = re.sub(r"\s*[—–-]\s*segment\s+\d+\s*/\s*\d+\s*", "", name, flags=re.I)
    name = re.sub(r"\bspine\b", "walkway", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) > 48:
        return name[:45] + "…"
    return name or nid


def _floor_words(code: str) -> str:
    c = (code or "").strip().upper()
    if c == "L02":
        return "Level 2"
    if c == "L03":
        return "Level 3"
    if c == "L04":
        return "Level 4"
    if c == "T1":
        return "Terminal 1"
    return c or ""

MILESTONE_KINDS = frozenset(
    {
        "entrance",
        "security",
        "gate",
        "food",
        "shopping",
        "baggage",
        "restroom",
        "service",
        "vertical",
        "junction",
    }
)

# User-facing buckets for any shop/dine category string from CSV / API.
COFFEE_SNACK = frozenset(
    {
        "coffee_shop",
        "qsr",
        "quick_bites",
        "snacks",
        "premium_bakery",
        "confectionary",
        "sweets_/_packed_foods",
    }
)
MEAL_BAR = frozenset({"bar_&_restaurant"})
DUTY_BEAUTY = frozenset(
    {
        "perfumes",
        "makeup_and_cosmetics",
        "wines_/_liquor",
        "jewellary",
        "men's_grooming",
        "health_and_beauty",
        "salon_/_spa",
    }
)


def _norm_cat(raw: str) -> str:
    return (raw or "").strip().lower().replace(" ", "_")


def user_experience_bucket(category: str, source: str) -> str:
    """Broad channel for copy: coffee_snack | meal | duty_beauty | shopping."""
    c = _norm_cat(category)
    if c in MEAL_BAR or "bar" in c or "restaurant" in c:
        return "meal"
    if c in COFFEE_SNACK or "coffee" in c or "tea" in c or "bakery" in c or "snack" in c:
        return "coffee_snack"
    if c in DUTY_BEAUTY or "perfume" in c or "wine" in c or "liquor" in c or "jewel" in c:
        return "duty_beauty"
    if "dining" in (source or "").lower() or "meal" in c:
        return "meal"
    return "shopping"


def bucket_heading(bucket: str) -> str:
    """Short label for UI chips."""
    return {
        "coffee_snack": "Coffee & snacks",
        "meal": "Sit-down meal",
        "duty_beauty": "Duty-free & beauty",
        "shopping": "Shops & gifts",
    }.get(bucket, "Nearby")


def bucket_tip_phrase(bucket: str) -> str:
    """Conversational line starter for tips (no jargon)."""
    return {
        "coffee_snack": "If you want coffee, tea, or a quick bite, look for",
        "meal": "If you’d like a proper meal or a bar, there’s",
        "duty_beauty": "For duty-free, perfume, or cosmetics, you’ll see",
        "shopping": "For shopping or gifts, you may pass",
    }.get(bucket, "Along this walk you’ll find")


def _short_label(node: dict[str, Any]) -> str:
    return passenger_place_name(node)


def pick_milestone_indices(path_nodes: list[dict[str, Any]]) -> list[int]:
    """Reduce long corridor chains to a few turning points for passengers."""
    if len(path_nodes) <= 2:
        return list(range(len(path_nodes)))
    n = len(path_nodes)
    ms = [0]
    last_kept = 0
    for i in range(1, n - 1):
        p = path_nodes[i]
        prev = path_nodes[i - 1]
        kind = str(p.get("kind") or "")
        zone_break = p.get("zone") != prev.get("zone")
        landmark = kind in MILESTONE_KINDS
        long_leg = (i - last_kept) >= 9
        if landmark or zone_break or long_leg:
            ms.append(i)
            last_kept = i
    if n - 1 not in ms:
        ms.append(n - 1)
    return sorted(set(ms))


def segment_minutes(edges: list[dict[str, Any]], i_from: int, i_to_idx: int) -> int:
    """Sum edge minutes walking from path node i_from to path node i_to_idx."""
    total = 0
    for e in range(i_from, i_to_idx):
        if e < len(edges):
            total += int(edges[e].get("minutes", 0))
    return max(total, 0)


def build_simple_journey(
    path_nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    total_time_minutes: int,
) -> dict[str, Any]:
    ms = pick_milestone_indices(path_nodes)
    bullets: list[str] = []
    if len(ms) == 1:
        bullets.append(
            f"You are already at {_short_label(path_nodes[0])} (about {total_time_minutes} min overall)."
        )
        return {
            "title": f"About {total_time_minutes} min",
            "subtitle": _short_label(path_nodes[0]),
            "bullets": bullets,
            "milestone_count": 1,
        }

    bullets.append(
        f"Start at {_short_label(path_nodes[0])}. The whole walk is about {total_time_minutes} minutes."
    )
    last_dest_label = _short_label(path_nodes[0])
    for s in range(len(ms) - 1):
        a, b = ms[s], ms[s + 1]
        m = segment_minutes(edges, a, b)
        dest = path_nodes[b]
        lab = _short_label(dest)
        main_repeat = lab.startswith("Main hall —") and last_dest_label.startswith("Main hall —")
        if main_repeat:
            tail = lab.removeprefix("Main hall —").strip()
            if s == len(ms) - 2:
                bullets.append(
                    f"Then move further through the main hall ({tail}) — about {m} more minutes."
                )
            else:
                bullets.append(
                    f"Continue through the main hall ({tail}) — about {m} minutes on this part."
                )
        elif s == len(ms) - 2:
            bullets.append(f"Then head to {lab} — about {m} more minutes.")
        else:
            bullets.append(f"Continue toward {lab} — about {m} minutes on this part.")
        last_dest_label = lab
    return {
        "title": f"About {total_time_minutes} min",
        "subtitle": f"{_short_label(path_nodes[0])} → {_short_label(path_nodes[-1])}",
        "bullets": bullets,
        "milestone_count": len(ms),
    }


def shops_along_path(path_node_ids: list[str], *, max_total: int = 10) -> dict[str, Any]:
    """Shops/dining whose graph anchor lies on the walking path, grouped for tips."""
    path_set = set(path_node_ids)
    shops = load_shops_t2_l02()

    order = ["coffee_snack", "meal", "duty_beauty", "shopping"]
    by_bucket: dict[str, list[dict[str, Any]]] = {k: [] for k in order}
    seen_ids: set[str] = set()
    for s in shops:
        gid = str(s.get("graph_node_id") or "").strip()
        if gid not in path_set:
            continue
        sid = str(s.get("shop_id") or "").strip()
        if not sid or sid in seen_ids:
            continue
        seen_ids.add(sid)
        cat = str(s.get("category") or "")
        src = str(s.get("source") or "")
        bucket = user_experience_bucket(cat, src)
        fl = str(s.get("floor") or "")
        h = {
            "shop_id": sid,
            "name_display": s.get("name_display"),
            "category": cat,
            "experience_bucket": bucket,
            "bucket_label": bucket_heading(bucket),
            "graph_node_id": gid,
            "floor": fl,
            "floor_display": _floor_words(fl),
            "listing_location": (s.get("listing_location") or "")[:120],
        }
        by_bucket.setdefault(bucket, []).append(h)

    flat: list[dict[str, Any]] = []
    for b in order:
        for h in by_bucket.get(b, [])[:4]:
            flat.append(h)
            if len(flat) >= max_total:
                break
        if len(flat) >= max_total:
            break

    tips: list[str] = []
    for b in order:
        items = by_bucket.get(b) or []
        if not items:
            continue
        names = ", ".join(str(x["name_display"]) for x in items[:3])
        intro = bucket_tip_phrase(b)
        tips.append(f"{intro} {names}.")

    total_on_path = sum(len(v) for v in by_bucket.values())
    return {
        "count_on_path": total_on_path,
        "by_bucket": {k: v[:5] for k, v in by_bucket.items() if v},
        "picks": flat,
        "tips": tips[:5],
    }
