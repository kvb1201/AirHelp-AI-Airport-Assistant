"""
Hard-coded safety / assistance intents (no RAG).

- Medical distress → route to ``t2_medical`` (Medical station).
- Lost property / baggage → route to ``t2_lost_found`` + helpline.
- Disoriented / general help / "I'm lost" → helpline first, then route to ``t2_information``.

Explicit walking requests (``take me to medical room``, ``where is lost and found``) are **not**
intercepted here so the normal navigation path can handle them.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Literal, Optional

from app.core.graph.node_mapper import coerce_to_graph_node_id
from app.services.navigation_service import get_route, resolve_node_id, resolve_place_label_to_graph_node

# Official CSMIA Information Desk copy (see ``csmia_information_desk_t2_source.json``).
CSMIA_HELPLINE = "1800-572-111111"

NODE_MEDICAL = "t2_medical"
NODE_INFORMATION = "t2_information"
NODE_LOST_FOUND = "t2_lost_found"
DEFAULT_START = "t2_entrance"

SpecialKind = Literal["medical", "lost_property", "disoriented_help"]


def _norm(msg: str) -> str:
    return (msg or "").strip().lower()


def _looks_like_explicit_nav_to_facility(t: str) -> bool:
    """User is asking for directions to a place, not declaring an emergency."""
    return bool(
        re.search(
            r"\b(?:take me|walk me|guide me|navigate|directions|route|path|way)\s+(?:to\s+)?",
            t,
            re.I,
        )
        or re.search(r"\bwhere\s+(?:is|are)\s+", t, re.I)
        or re.search(r"\bhow\s+do\s+i\s+(?:get|go)\s+to\s+", t, re.I)
    )


def classify_special_assistance(message: str) -> Optional[SpecialKind]:
    t = _norm(message)
    if len(t) < 3:
        return None

    explicit_nav = _looks_like_explicit_nav_to_facility(t)

    # --- Medical (symptoms / urgent help; not "take me to the medical room") ---
    symptom_or_urgent = any(
        p in t
        for p in (
            "chest pain",
            "can't breathe",
            "cant breathe",
            "cannot breathe",
            "trouble breathing",
            "difficulty breathing",
            "choking",
            "bleeding",
            "blood loss",
            "passed out",
            "passing out",
            "fainted",
            "fainting",
            "seizure",
            "unconscious",
            "severe allergic",
            "anaphylaxis",
            "heart attack",
            "stroke",
            "broken bone",
            "think i'm having",
            "think i am having",
            "severe pain",
            "unbearable pain",
            "badly hurt",
            "badly injured",
        )
    )
    medical_help = any(
        p in t
        for p in (
            "medical emergency",
            "need a doctor",
            "need doctor",
            "call a doctor",
            "call doctor",
            "call an ambulance",
            "call ambulance",
            "need ambulance",
            "need medical",
            "need medical help",
            "first aid",
            "first-aid",
            "sick and need",
            "feel sick",
            "feeling sick",
            "throwing up",
            "vomiting",
            "severe nausea",
            "injured",
            "i'm hurt",
            "i am hurt",
            "im hurt",
            "badly hurt",
            "someone hurt",
            "someone is hurt",
            "need nurse",
            "need medic",
            "defibrillator",
            "aed",
            "allergic reaction",
            "overdose",
            "suicidal",
            "self harm",
            "panic attack",
            "pregnant and bleeding",
            "baby is sick",
            "child is sick",
            "elderly fell",
            "fell and can't get up",
        )
    )
    medical_soft = any(
        p in t
        for p in (
            "medical help",
            "medical aid",
            "medical assistance",
            "see a medic",
            "airport clinic",
            "airport medical",
            "pharmacy urgently",
            "urgent medicine",
            "need medicine urgently",
            "prescription emergency",
        )
    )
    # Symptoms always escalate. For wording-only medical asks, do not hijack explicit walking queries.
    if symptom_or_urgent:
        return "medical"
    if not explicit_nav and (medical_help or medical_soft):
        return "medical"

    # --- Lost property (not "I am lost") ---
    lost_property = bool(
        re.search(
            r"\b(lost|misplaced|left behind|forgot)\s+(my|our|the)\b",
            t,
        )
        or re.search(
            r"\b(lost|missing)\s+(bag|luggage|suitcase|backpack|wallet|phone|passport|laptop|keys)\b",
            t,
        )
        or "lost and found" in t
        or "lost & found" in t
        or "lost property" in t
        or "baggage is lost" in t
        or "luggage is lost" in t
        or "missing bag" in t
        or "missing luggage" in t
    )
    if lost_property and not explicit_nav:
        return "lost_property"

    # --- Disoriented / need human help ---
    disoriented = bool(
        re.search(r"\b(i'?m|i am)\s+lost\b", t)
        or re.search(r"\bim\s+lost\b", t)
        or re.search(r"\bhelp\s+me\s+i\s*'?m\s+lost\b", t)
        or re.search(r"\bhelp\s+i\s*'?m\s+lost\b", t)
        or "feel lost" in t
        or "feeling lost" in t
        or "stranded" in t
        or "where am i" in t
        or "don't know where to go" in t
        or "do not know where to go" in t
        or "can't find the exit" in t
        or "cant find the exit" in t
        or "can't find my gate" in t
        or "cant find my gate" in t
        or "confused at the airport" in t
        or "so confused" in t
        or re.search(r"\bneed\s+help\b.*\b(lost|confused|stuck|scared|alone|stranded)\b", t)
        or re.search(r"\bhelp\b.*\b(i\s*'?m|i am)\s+lost\b", t)
        or re.search(r"\bplease\s+help\b.*\b(lost|confused|stuck|scared)\b", t)
        or "don't know where i am" in t
        or "do not know where i am" in t
        or "airport help" in t
        or "need airport staff" in t
        or "speak to someone" in t
        or "talk to someone" in t
        or ("customer service" in t and "complaint" not in t)
    )
    if disoriented and not explicit_nav:
        return "disoriented_help"

    return None


def _resolve_start_graph(location_label: Optional[str]) -> str:
    raw = (location_label or "").strip()
    if not raw:
        return DEFAULT_START
    gid = coerce_to_graph_node_id(raw)
    if gid:
        return gid
    g = resolve_place_label_to_graph_node(raw)
    if g:
        return g
    resolved, _ = resolve_node_id(raw, role="start")
    return resolved or DEFAULT_START


def _format_route_block(nav: Dict[str, Any]) -> str:
    if not nav.get("ok"):
        hint = (nav.get("hint") or "").strip()
        if hint:
            return f"Walking directions could not be computed ({hint}). Use the map / facilities list to reach the hub."
        return "Walking directions could not be computed from your current pin. Use the map or Facilities to open that hub."

    steps = nav.get("steps") or []
    if not steps:
        return "Route steps were not available; open the map for this destination."

    mins = nav.get("total_time_minutes", "?")
    lines = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
    return f"Walking route (~{mins} min walk):\n{lines}"


def try_special_assistance_response(
    *,
    loc_msg: str,
    user_context: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    kind = classify_special_assistance(loc_msg)
    if not kind:
        return None

    loc_label = (user_context.get("source") or user_context.get("location") or "").strip() or None
    start_graph = _resolve_start_graph(loc_label)

    em = "Life-threatening emergency in India: dial **112** from any phone.\n\n"

    if kind == "medical":
        goal = NODE_MEDICAL
        header = (
            f"{em}"
            "If you can, alert airport security or the nearest staff member immediately.\n\n"
            f"**CSMIA 24/7 helpline:** {CSMIA_HELPLINE}\n\n"
            "Routing you toward the **Medical station** (first aid / referral)."
        )
    elif kind == "lost_property":
        goal = NODE_LOST_FOUND
        header = (
            f"{em}"
            f"**Lost & found:** use the desk or official CSMIA channels to report items.\n"
            f"**24/7 helpline:** {CSMIA_HELPLINE}\n\n"
            "Walking directions toward **Lost & found** (main desk hub on the map):"
        )
    else:
        goal = NODE_INFORMATION
        header = (
            f"{em}"
            f"**Airport helpline (24/7):** {CSMIA_HELPLINE}\n"
            "**Information & customer service** can orient you, print basics, and escalate.\n\n"
            "Walking directions toward the main **information / help desk** hub:"
        )

    nav = get_route(start_graph, goal, local_hour=12, busy_terminal=False)
    start_out = nav.get("start_id") or start_graph
    goal_out = nav.get("goal_id") or goal

    message = f"{header}\n\n{_format_route_block(nav)}"
    user_context["mode"] = "navigation"

    return {
        "type": "navigation",
        "intent": "navigation",
        "message": message,
        "data": {
            "navigation": nav,
            "start": start_out,
            "end": goal_out,
            "special_assistance": kind,
        },
        "context": user_context,
    }
