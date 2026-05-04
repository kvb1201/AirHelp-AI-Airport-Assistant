"""
Hard-coded safety / assistance intents (no RAG).

- Medical distress → route to ``t2_medical`` (Medical station).
- Lost property / baggage (including ``my baggage has been lost``, ``where is my luggage``, delayed/damaged bags) → ``t2_lost_found`` + helpline + flash.
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

# Official facility pages (``facilities_bom.csv`` page_url patterns).
CRISIS_WEB_URL: Dict[str, str] = {
    "medical": "https://csmia-mumbai.adaniairports.com/en/airport-facilities/special-assistance",
    "lost_property": "https://csmia-mumbai.adaniairports.com/en/airport-facilities/lost-and-found-services",
    "disoriented_help": "https://csmia-mumbai.adaniairports.com/en/airport-facilities/information-desk",
}

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


_BARE_HELP_OR_EMERGENCY = frozenset(
    {
        "help",
        "please help",
        "help please",
        "need help",
        "need help now",
        "need urgent help",
        "emergency",
        "emergency help",
        "help emergency",
        "urgent help",
        "urgent",
        "immediate help",
        "need immediate help",
        "i need help immediately",
        "need help immediately",
        "help me immediately",
        "i need help right now",
        "need help right now",
        "help me right now",
        "sos",
        "911",
        "112",
        "send help",
        "airport emergency",
        "i need help",
        "we need help",
        "can anyone help",
        "anyone there",
        "someone help",
        "somebody help",
        "assist me",
        "need assistance",
        "get me help",
        "call for help",
    }
)


def _is_short_standalone_help_or_emergency(t: str) -> bool:
    """Single-line cries for help (voice UI often sends just ``help`` / ``emergency``)."""
    s = t.strip().lower()
    s = re.sub(r"^[\s.,!?;:]+|[\s.,!?;:]+$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > 72 or not s:
        return False
    if s in _BARE_HELP_OR_EMERGENCY:
        return True
    if re.fullmatch(r"(please\s+)?help(\s+please)?", s):
        return True
    if re.fullmatch(r"(please\s+)?emergency(\s+please)?", s):
        return True
    if re.fullmatch(r"emergency\s+help", s):
        return True
    if re.fullmatch(r"help\s+emergency", s):
        return True
    # Common misspelling / voice errors
    if re.fullmatch(r"i\s+need\s+help\s+imediately", s):
        return True
    return False


# Urgent phrasing (not bare "need help" + unrelated "now" later — avoid false positives).
_URGENT_HELP_TAIL = (
    r"(?:right\s+now|immediately|imediately|asap|urgently|instantly|right\s+away|at\s+once)"
)


def _has_urgent_help_wording(t: str) -> bool:
    """Longer messages that still mean immediate human / airport help (edge cases for chat)."""
    if not t or len(t) > 280:
        return False
    return bool(
        re.search(rf"\b(i\s+)?need\s+help\s+{_URGENT_HELP_TAIL}\b", t, re.I)
        or re.search(rf"\bhelp\s+me\s+{_URGENT_HELP_TAIL}\b", t, re.I)
        or re.search(r"\b(i\s+)?need\s+(?:immediate|urgent)\s+help\b", t, re.I)
        or re.search(r"\bneed\s+(?:immediate|urgent)\s+assistance\b", t, re.I)
        or re.search(r"\bhelp\s+immediately\b", t, re.I)
        or re.search(rf"\bplease\s+help\s+me\s+{_URGENT_HELP_TAIL}\b", t, re.I)
        or re.search(r"\b(i\s+)?need\s+help\s+now\b(?!\s+that\b)", t, re.I)
    )


def _lost_baggage_or_item_issue(t: str) -> bool:
    """
    Passenger reports missing / delayed / damaged checked or carry-on items, or stolen valuables.

    Matched **even if** the user also uses navigation phrasing (``where is my luggage``, ``how do I get
    to report``) so they still get the lost-property flash + helpline + desk route.
    """
    if not t:
        return False
    item = r"(?:baggage|luggage|checked\s*bags?|suitcase|backpack|carry[\s-]*on|carryon|bags?|wallet|passport|phones?|laptops?|keys|documents?)"
    return bool(
        re.search(
            rf"\b(my|our|the)\s+{item}\s+(has|have|is|was|got)\s+(been\s+)?lost\b",
            t,
            re.I,
        )
        or re.search(
            rf"\b{item}\s+(has|have|is|was|got)\s+(been\s+)?lost\b",
            t,
            re.I,
        )
        or re.search(
            rf"\b(my|our|the)?\s*{item}\s+(has|have)\s+not\s+arrived\b",
            t,
            re.I,
        )
        or re.search(rf"\b(my|our|the)?\s*{item}\s+(is|are)\s+missing\b", t, re.I)
        or re.search(
            r"\b(they|the\s+airline|airline|carrier|airport)\s+lost\s+my\b",
            t,
            re.I,
        )
        or re.search(
            rf"\b(my\s+)?{item}\s+never\s+(?:came|came\s+through|showed\s+up|arrived|appeared)\b",
            t,
            re.I,
        )
        or re.search(
            rf"\b(can'?t|cannot)\s+find\s+my\s+(?:bag|bags|luggage|baggage|suitcase|backpack)\b",
            t,
            re.I,
        )
        or re.search(
            rf"\bwhere\s+(?:is|are)\s+my\s+(?:baggage|luggage|suitcase|checked\s*bags?|bags?)\b",
            t,
            re.I,
        )
        or re.search(
            r"\b(delayed|missing)\s+(?:baggage|luggage|checked\s*bag)\b",
            t,
            re.I,
        )
        or re.search(
            r"\b(baggage|luggage)\s+(?:delay|claim|damaged|broken|destroyed|mishandled)\b",
            t,
            re.I,
        )
        or re.search(
            r"\b(stolen|robbed|pickpocket|pick[\s-]*pocket)\s+(?:my|our)\s+(?:bag|wallet|phone|passport|laptop)\b",
            t,
            re.I,
        )
        or re.search(
            r"\b(my|our)\s+(?:lost|missing)\s+(?:wallet|passport|phone|laptop|keys|bag|bags|luggage)\b",
            t,
            re.I,
        )
        or re.search(
            r"\bi\s+(?:lost|misplaced)\s+(?:my|our|the|a|an)\b",
            t,
            re.I,
        )
        or re.search(
            r"\b(left|forgot|left behind)\s+(?:my|our|the)\s+(?:bag|luggage|baggage|suitcase|wallet|phone|passport|laptop)\b",
            t,
            re.I,
        )
        or re.search(
            r"\bwithout\s+(?:my|our)\s+(?:checked\s*)?(?:bag|bags|luggage|baggage)\b",
            t,
            re.I,
        )
        or re.search(
            r"\b(my|our)\s+(?:bag|bags|luggage|baggage|suitcase)\s+(is|are)\s+(gone|missing|not\s+here|nowhere)\b",
            t,
            re.I,
        )
    )


# Pulled from facilities_bom.csv (information desk, helpline, help phones, lost & found, special assistance).
FACILITY_FLASH_BY_KIND: Dict[SpecialKind, list[str]] = {
    "medical": [
        "Special Assistance & medical escalation: official CSMIA Special Assistance page (link below).",
        "24/7 helpline on the Information Desk listing can coordinate responders — same number as the flash card.",
    ],
    "lost_property": [
        "Lost & Found (T2): report delayed, damaged, or missing checked bags and left items — official Lost & Found services page.",
        "Information desk helpline (24/7) on the same airport listing can escalate baggage irregularities if the desk is busy.",
        "Use the helpline above if you cannot reach the desk or need an urgent baggage status update.",
    ],
    "disoriented_help": [
        "Information desks (T2): arrivals, departure curbside (lanes 1–2), check-in islands, retail on L3/L4 — see Information Desk page.",
        "Help phones (airport facilities listing): use any marked help phone near the information hub for staff.",
        "Lost & Found — for missing bags or items; Special Assistance — wheelchairs, escorts, mobility — separate official pages.",
    ],
}


def classify_special_assistance(message: str) -> Optional[SpecialKind]:
    t = _norm(message)
    if not t:
        return None

    explicit_nav = _looks_like_explicit_nav_to_facility(t)

    if not explicit_nav and (
        _is_short_standalone_help_or_emergency(t) or _has_urgent_help_wording(t)
    ):
        return "disoriented_help"

    if len(t) < 3:
        return None

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

    # --- Lost property / baggage (not disoriented "I am lost" without a bag/item story) ---
    lost_baggage_crisis = _lost_baggage_or_item_issue(t)
    lost_property_other = bool(
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
        or "misplaced baggage" in t
        or "misplaced luggage" in t
        or "baggage mishandling" in t
        or "pir claim" in t
        or "property irregularity" in t
    )
    lost_desk_query = "lost and found" in t or "lost & found" in t
    # Desk / baggage issues: always escalate (including ``where is lost and found`` — still helpline + route).
    if lost_baggage_crisis or lost_desk_query or (lost_property_other and not explicit_nav):
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
        or _has_urgent_help_wording(t)
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
            "**Information desks & help phones** (see flash screen) match official T2 facility listings.\n"
            "**Information & customer service** can orient you, print basics, and escalate.\n\n"
            "Walking directions toward the main **information / help desk** hub:"
        )

    nav = get_route(start_graph, goal, local_hour=12, busy_terminal=False)
    start_out = nav.get("start_id") or start_graph
    goal_out = nav.get("goal_id") or goal

    message = f"{header}\n\n{_format_route_block(nav)}"
    user_context["mode"] = "navigation"

    headlines = {
        "medical": "Medical assistance",
        "lost_property": "Lost & found",
        "disoriented_help": "Airport help & information",
    }
    crisis_contact: Dict[str, Any] = {
        "headline": headlines[kind],
        "helpline": CSMIA_HELPLINE,
        "helpline_label": "CSMIA 24/7 helpline",
        "emergency_dial": "112",
        "emergency_label": "Life-threatening emergency (India)",
        "website_url": CRISIS_WEB_URL[kind],
        "website_label": "Official CSMIA page",
        "facility_hints": FACILITY_FLASH_BY_KIND.get(kind, []),
    }
    if kind == "disoriented_help":
        crisis_contact["flash_lede"] = (
            "Need someone now? Call the helpline or use a help phone first (see facility notes). "
            "Life-threatening emergency in India: dial 112. Walking directions stay in the chat below."
        )

    return {
        "type": "navigation",
        "intent": "navigation",
        "message": message,
        "data": {
            "navigation": nav,
            "start": start_out,
            "end": goal_out,
            "special_assistance": kind,
            "crisis_contact": crisis_contact,
        },
        "context": user_context,
    }
