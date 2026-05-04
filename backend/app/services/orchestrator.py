import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.llm_service import call_llm
from app.services.navigation_service import (
    get_route,
    goal_from_rag_snippets,
    plan_navigation_from_chat,
    resolve_node_id,
    resolve_place_label_to_graph_node,
    resolve_shop_name_to_graph_node,
    resolve_walking_goal_id,
)
from app.services.rag_service import search
from app.services.locating_engine import SERVICE_LABELS, locate_from_query
from app.services.context_engine import update_context
from app.services.context_normalizer import normalize_chat_context
from app.services.query_preprocess import compose_navigation_message, prepare_for_locate_and_context
from app.services.special_assistance_intents import try_special_assistance_response
from app.core.graph.airport_data import NODES
from app.core.graph.node_mapper import coerce_to_graph_node_id
from app.core.llm.prompts import SYSTEM_PROMPT
from app.utils.logger import logger


PROJECT_ROOT = Path(__file__).resolve().parents[3]
# Prefer the workspace-wide data/airport/flights.json, fallback to packaged catalog
FLIGHT_CATALOG_PATHS = [
    PROJECT_ROOT.parents[0] / "data" / "airport" / "flights.json",
    PROJECT_ROOT / "backend" / "app" / "data" / "mumbai_t2_catalog.json",
]
IST = timezone(timedelta(hours=5, minutes=30))
_FLIGHT_CATALOG_CACHE: list[dict[str, Any]] | None = None
_FLIGHT_REFERENCE_RE = re.compile(r"\b([A-Z]{2,3})[\s\-]?(\d{1,4})\b", re.IGNORECASE)


# -------------------------------
# 🔥 Intent Normalization
# -------------------------------
def normalize_intent(intent: str) -> str:
    if not intent:
        return "general"

    intent_lower = intent.lower()

    recommendation_intents = {
        "food", "coffee", "restaurant", "eat", "dining",
        "shop", "shopping", "buy", "store", "retail",
        "lounge", "relax", "rest",
        "atm", "money", "cash",
        "wifi", "internet", "charging",
        "restroom", "toilet", "washroom",
        "prayer", "meditation",
        "facility", "service",
        "recommendation"
    }

    if intent_lower in recommendation_intents:
        return "recommendation"

    if intent_lower == "explore":
        return "explore"

    if intent_lower in {"navigation", "navigate", "direction", "route"}:
        return "navigation"

    return "general"


# -------------------------------
# 🔹 Intent Detection (fallback)
# -------------------------------
def detect_intent(message: str) -> str:
    msg = message.lower()

    if any(word in msg for word in [
        "gate",
        "navigate",
        "direction",
        "reach",
        "walk",
        "how do i get",
        "how do i go",
        "how to get",
        "where is",
        "where's",
        "point me",
        "which way",
        "route to",
        "path to",
        "take me",
    ]):
        return "navigation"

    if any(phrase in msg for phrase in [
        "what can i do", "things to do", "explore",
        "nearby", "around",
    ]):
        return "explore"

    if any(word in msg for word in [
        "food", "eat", "coffee", "restaurant",
        "shop", "buy", "lounge", "atm", "wifi",
        "restroom", "prayer", "facility"
    ]):
        return "recommendation"

    if any(word in msg for word in [
        "time", "late", "delay", "boarding", "takeoff", "departure", "flight"
    ]):
        return "time_check"

    return "general"


# -------------------------------
# 🔹 Follow-up detection
# -------------------------------
def _is_followup_query(msg: str) -> bool:
    msg = msg.lower().strip()

    return msg in [
        "show options",
        "options",
        "more",
        "more options",
        "what else",
        "anything else",
    ]


# -------------------------------
# 🔥 Query Rewriting
# -------------------------------
def _rewrite_query(user_input: str, context: Dict) -> str:
    msg = user_input.lower().strip()

    intent = context.get("intent")
    location = context.get("source")
    behavior = context.get("behavior")

    # -------------------------------
    # 🔥 FOLLOW-UP (STRONG CONTROL)
    # -------------------------------
    if _is_followup_query(msg) and intent:
        if location:
            return f"{intent} options in {location}"
        return f"{intent} options"

    # -------------------------------
    # 🔥 INTENT-SPECIFIC REWRITES
    # -------------------------------
    if intent == "food":
        if behavior == "quick":
            return f"fast food options in {location}"
        return f"food options in {location}"

    if intent == "coffee":
        return f"coffee shops in {location}"

    if intent == "restroom":
        return f"restrooms near {location}"

    if intent == "lounge":
        return f"lounges in {location}"

    if intent == "atm":
        return f"ATMs in {location}"

    if intent == "wifi":
        return f"wifi services in {location}"

    # -------------------------------
    # 🔥 NAVIGATION TYPE
    # -------------------------------
    if intent == "navigation":
        return user_input

    # -------------------------------
    # 🔹 FALLBACK
    # -------------------------------
    return user_input


# -------------------------------
# 🔹 Extract Terminal
# -------------------------------
def _extract_terminal_for_rag(location: Optional[str]) -> Optional[str]:
    if not location:
        return None

    loc = location.lower().strip()

    m = re.search(r"terminal[_\s]*([1-3])", loc)
    if m:
        return f"terminal_{m.group(1)}"

    m = re.match(r"^t([1-3])(?:[_\s]|$)", loc)
    if m:
        return f"terminal_{m.group(1)}"

    return None


# -------------------------------
# 🔹 Query Builder
# -------------------------------
def _build_search_query(user_input: str, location: Optional[str], intent_type: str) -> str:
    if intent_type == "explore":
        return f"things to do in {location} airport" if location else "things to do in airport"

    if intent_type == "recommendation":
        return f"{user_input} in {location}" if location else user_input

    return user_input


def _normalize_flight_key(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def _parse_time_to_minutes(value: str | None) -> int | None:
    if not value:
        return None

    text = value.strip().upper()
    match = re.match(r"^(\d{1,2}):(\d{2})(?:\s*([AP]M))?$", text)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2))
    suffix = match.group(3)

    if suffix == "AM":
        if hour == 12:
            hour = 0
    elif suffix == "PM" and hour != 12:
        hour += 12

    return hour * 60 + minute


def _format_minutes_of_day(minutes: int | None) -> str:
    if minutes is None:
        return "unknown"
    hour = (minutes // 60) % 24
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


def _load_flight_catalog() -> list[dict[str, Any]]:
    global _FLIGHT_CATALOG_CACHE
    if _FLIGHT_CATALOG_CACHE is not None:
        return _FLIGHT_CATALOG_CACHE

    payload = None
    used_path = None
    # Try configured catalog paths in order
    for p in FLIGHT_CATALOG_PATHS:
        try:
            if p.exists():
                with p.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                    used_path = p
                    break
        except OSError:
            continue

    if payload is None:
        logger.warning("No flight catalog found at configured paths; returning empty list")
        _FLIGHT_CATALOG_CACHE = []
        return _FLIGHT_CATALOG_CACHE

    logger.info(f"Loaded flight catalog from {used_path}")

    # Normalize different catalog formats to a common shape with 'flight_number'
    flights: list[dict[str, Any]] = []

    if isinstance(payload, dict) and "flights" in payload and isinstance(payload.get("flights"), list):
        # Existing packaged catalog format
        flights = payload.get("flights", [])
    elif isinstance(payload, list):
        # Likely the data/airport/flights.json format
        for item in payload:
            # Prefer explicit flight_id, else try flight_number
            flight_id = item.get("flight_id") or item.get("flight_number")
            flight_number = None
            if flight_id:
                m = re.match(r"^([A-Z]{2,3})[_\-]?(\d{1,4})", str(flight_id))
                if m:
                    flight_number = f"{m.group(1)} {m.group(2)}"
                else:
                    flight_number = str(flight_id)

            timings = item.get("timings") or {}
            departure = timings.get("scheduled") or item.get("departure_time") or None
            boarding = timings.get("boarding") or item.get("boarding_time") or None

            flights.append({
                "flight_number": flight_number,
                "boarding_time": boarding,
                "departure_time": departure,
                "terminal": item.get("terminal") or item.get("terminal_name"),
                "gate_display": item.get("gate") or item.get("gate_display"),
            })
    else:
        # Unknown format
        logger.warning("Unrecognized flight catalog format; returning empty list")
        _FLIGHT_CATALOG_CACHE = []
        return _FLIGHT_CATALOG_CACHE

    _FLIGHT_CATALOG_CACHE = flights
    return _FLIGHT_CATALOG_CACHE


def _extract_flight_reference(user_input: str, user_context: Dict[str, Any]) -> str | None:
    for key in ("flight_number", "flight_id"):
        value = user_context.get(key)
        if value:
            return str(value)

    match = _FLIGHT_REFERENCE_RE.search(user_input)
    if match:
        return f"{match.group(1).upper()} {match.group(2)}"

    return None


def _find_flight_record(reference: str | None, user_context: Dict[str, Any]) -> dict[str, Any] | None:
    boarding_time = user_context.get("boarding_time")
    departure_time = user_context.get("departure_time")

    if boarding_time or departure_time:
        return {
            "flight_number": reference or user_context.get("flight_number") or "your flight",
            "boarding_time": boarding_time,
            "departure_time": departure_time,
            "terminal": user_context.get("terminal") or user_context.get("location") or "T2",
            "gate_display": user_context.get("gate") or user_context.get("destination"),
        }

    if not reference:
        return None

    ref_key = _normalize_flight_key(reference)
    for item in _load_flight_catalog():
        item_key = _normalize_flight_key(item.get("flight_number"))
        if item_key == ref_key:
            return dict(item)

    return None


def _build_time_nudges(flight: dict[str, Any]) -> tuple[str, list[dict[str, str]]]:
    flight_number = flight.get("flight_number") or "Your flight"
    terminal = flight.get("terminal") or "T2"
    boarding_time = flight.get("boarding_time")
    departure_time = flight.get("departure_time")

    boarding_minutes = _parse_time_to_minutes(boarding_time)
    departure_minutes = _parse_time_to_minutes(departure_time)

    if boarding_minutes is None and departure_minutes is not None:
        boarding_minutes = max(departure_minutes - 45, 0)
        boarding_time = _format_minutes_of_day(boarding_minutes)
    elif departure_minutes is None and boarding_minutes is not None:
        departure_minutes = boarding_minutes + 45
        departure_time = _format_minutes_of_day(departure_minutes)

    if boarding_minutes is None:
        boarding_minutes = 0
    if departure_minutes is None:
        departure_minutes = boarding_minutes + 45

    events = [
        {"label": "Head to security", "minutes": max(departure_minutes - 120, 0)},
        {"label": "Go to gate", "minutes": max(boarding_minutes - 45, 0)},
        {"label": "Final call", "minutes": max(boarding_minutes - 10, 0)},
    ]

    formatted_events = [
        {"time": _format_minutes_of_day(event["minutes"]), "nudge": event["label"]}
        for event in events
    ]

    now = datetime.now(IST)
    now_minutes = now.hour * 60 + now.minute
    due = [event for event in events if now_minutes >= event["minutes"]]
    next_event = next((event for event in events if now_minutes < event["minutes"]), None)

    lines = [f"{flight_number} · {terminal}"]
    for event in formatted_events:
        lines.append(f"- {event['time']}: {event['nudge']}")

    if due:
        lines.append("")
        lines.append(f"Right now: {due[-1]['label']}.")
    elif next_event:
        lines.append("")
        lines.append(f"Next: {next_event['label']} at {_format_minutes_of_day(next_event['minutes'])}.")

    return "\n".join(lines), formatted_events


# -------------------------------
# 🔹 Format Single Result
# -------------------------------
def _format_single_result(r: Dict[str, Any]) -> str:
    name = r.get("name")
    loc = r.get("location", "")
    desc = (r.get("description") or "").strip()

    lines = []

    if loc:
        lines.append(f"{name} ({loc})")
    else:
        lines.append(name)

    # Never paste internal RAG / embedding-debug blobs into chat.
    if desc and not any(
        x in desc
        for x in (
            "internal key",
            "Traveler-fit notes",
            "RAG grouping for food search",
            "CSV category:",
        )
    ):
        lines.append("\n" + (desc[:280] + ("…" if len(desc) > 280 else "")))
    else:
        lines.append("\nOpening the map with walking directions to this place.")

    return "\n".join(lines)


# -------------------------------
# 🔹 Format Multi Results
# -------------------------------
def _format_multi_results(results: List[Dict]) -> str:
    lines = ["Here are some options:\n"]

    for r in results:
        line = f"• {r.get('name')}"
        if r.get("location"):
            line += f" ({r['location']})"
        lines.append(line)

    return "\n".join(lines)


# ===============================
# 🚀 NAVIGATION INTEGRATION
# ===============================


# -------------------------------
# 1. Navigation Trigger Detection
# -------------------------------
def _is_navigation_request(msg: str) -> bool:
    """Detect if the user is asking for navigation/directions."""
    m = msg.lower().strip()
    triggers = [
        "navigate",
        "take me",
        "directions",
        "how do i go",
        "how do i get",
        "how to get",
        "how to go",
        "route",
        "walk me to",
        "walk me ",
        "guide me to",
        "guide me ",
        "redirect",
        "redirection",
        "show me the way",
        "path to",
        "way to",
        "want to go to",
        "going to",
        "need to get to",
        "need to go to",
        "head to",
        "heading to",
        "get me to",
        "bring me to",
        "lead me to",
        "go to",  # e.g. "want to go to …", "go to gate B12"
        "where is",
        "where's",
        "wheres",
        "point me to",
        "point me ",
        "which way",
        "help me get",
        "help me find",
        "find my way",
        "need directions",
        "looking for directions",
        "can you get me",
        "drop me at",
        "send me to",
    ]
    if any(t in m for t in triggers):
        return True
    # "from gate 5 to security" style
    if re.search(r"\bfrom\s+.{2,60}\s+to\s+.{2,60}\b", m):
        return True
    return False


def _is_place_to_place_request(msg: str) -> bool:
    """``lenskart to haldiram`` or ``from lenskart to haldiram`` (no explicit ``take me`` / ``navigate``)."""
    low = (msg or "").strip().lower()
    if len(low) < 5:
        return False
    a, b = _parse_place_to_place(msg)
    if not a or not b:
        return False
    if any(
        x in low
        for x in (
            "take me",
            "navigate",
            "walk me",
            "guide me",
            "directions to",
            "route to",
            "path to",
            "how do i get",
            "how do i go",
            "get me to",
            "bring me to",
            "lead me to",
            "show me the way",
        )
    ):
        return False
    return True


_BAD_PTP_LEFT = re.compile(
    r"^(i|we|you)\s+(want|need|would|have|try|am|was|were|like)\b",
    re.I,
)


def _parse_place_to_place(msg: str) -> tuple[Optional[str], Optional[str]]:
    """Last ``<place> to <place>`` span wins so leading filler does not break parsing."""
    raw = (msg or "").strip()
    if len(raw) < 3:
        return None, None
    pat = re.compile(
        r"\b([a-z0-9][a-z0-9\s\-'’]{0,120}?)\s+to\s+([a-z0-9][a-z0-9\s\-'’]{1,120})\b",
        re.I,
    )
    last: Optional[tuple[str, str]] = None
    for mm in pat.finditer(raw):
        a, b = mm.group(1).strip(), mm.group(2).strip()
        a = re.sub(r"^(?:from|starting at|start at)\s+", "", a, flags=re.I).strip()
        if len(a) < 2 or len(b) < 2:
            continue
        if _BAD_PTP_LEFT.match(a):
            continue
        if len(a.split()) > 10 or len(b.split()) > 10:
            continue
        # Avoid "trying to get to haldiram" → a ends with get/go
        if re.search(r"\b(get|go)\s*$", a, re.I):
            continue
        last = (a, b)
    if not last:
        return None, None
    return last


# -------------------------------
# 2. Node Mapping
# -------------------------------
def _map_to_node(location_str: str) -> str:
    """
    Map labels toward graph node IDs for the navigation intercept.

    RAG / client may send ``node-t2-entrance`` or ``t2_ne_sp_14``. Those must reach
    ``get_route`` intact: stripping punctuation here used to turn ``node-t2-entrance``
    into ``nodet2entrance`` (unmappable). Resolve via ``node_mapper`` first.
    """
    if not location_str:
        return "entrance"

    raw = location_str.strip()
    gid = coerce_to_graph_node_id(raw)
    if gid:
        return gid

    loc = raw.lower()

    # ``gate b12`` → ``gate_b12`` (legacy pier). ``gate 45`` / ``45`` → numeric segregation key.
    gate_match = re.match(r"gate\s+([ab])\s*(\d{1,2})\b", loc)
    if gate_match:
        return f"gate_{gate_match.group(1)}{gate_match.group(2)}"
    gate_match = re.match(r"gate\s+(\d{1,2})\b", loc)
    if gate_match:
        return f"gate_num_{int(gate_match.group(1))}"
    if re.fullmatch(r"\d{1,2}", loc.strip()):
        return f"gate_num_{int(loc.strip())}"

    # Known landmark mappings
    known = {
        "food court": "food_court",
        "food_court": "food_court",
        "security": "security",
        "security checkpoint": "security",
        "entrance": "entrance",
        "main entrance": "entrance",
        "baggage claim": "baggage",
        "baggage": "baggage",
        "check-in": "checkin",
        "checkin": "checkin",
        "check in": "checkin",
        "restroom": "restroom",
        "washroom": "restroom",
        "toilet": "restroom",
        "lounge": "lounge",
        "duty free": "duty_free",
        "duty-free": "duty_free",
        "information": "info",
        "info desk": "info",
        "medical": "medical",
        "atm": "atm",
    }

    if loc in known:
        return known[loc]

    # Generic: replace spaces/hyphens with underscores
    normalized = re.sub(r"[\s\-]+", "_", loc)
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)

    return normalized if normalized else "entrance"


# -------------------------------
# 3a. Vague / placeholder destinations (do not call the graph router)
# -------------------------------
_VAGUE_DESTINATION_EXACT = frozenset(
    {
        "someplace",
        "somewhere",
        "anywhere",
        "whatever",
        "idk",
        "dunno",
        "any",
        "there",
        "it",
        "that",
        "this",
        "something",
        "anything",
        "wherever",
        "you",
        "you pick",
        "your choice",
        "a place",
        "place",
        "somewhere nice",
        "anywhere nice",
        "some place",
        "any place",
    }
)

# Strip trailing "… to eat / for food" so "someplace to eat" is treated like "someplace".
_FOOD_OR_EXPLORATION_TAIL = re.compile(
    r"\s+(?:"
    r"to\s+eat|to\s+drink|to\s+snack|"
    r"for\s+food|for\s+lunch|for\s+dinner|for\s+breakfast|for\s+a\s+meal|"
    r"to\s+get\s+food|for\s+something\s+to\s+eat|to\s+grab\s+(?:a\s+)?(?:bite|food)|"
    r"for\s+coffee|for\s+a\s+coffee|to\s+have\s+coffee|"
    r"that\s+serves\s+food|with\s+food|"
    r"to\s+hang\s+out|to\s+chill|to\s+rest"
    r")\s*$",
    re.I,
)

_VAGUE_LEADING = re.compile(
    r"^(someplace|somewhere|anything|something|anywhere|whatever|"
    r"some\s+place|any\s+place|any\s+thing)\b",
    re.I,
)


def _normalize_destination_for_vague_check(raw: str) -> str:
    s = str(raw).strip().lower()
    s = re.sub(r"^(?:uh|um|er)\b\s*", "", s)
    s = _FOOD_OR_EXPLORATION_TAIL.sub("", s).strip()
    s = re.sub(r"[?!.,]+$", "", s).strip()
    return s


def _is_vague_destination(raw: Optional[str]) -> bool:
    if not raw or not str(raw).strip():
        return True
    s = _normalize_destination_for_vague_check(raw)
    if len(s) <= 1:
        return True
    if s in _VAGUE_DESTINATION_EXACT:
        return True
    if re.fullmatch(r"(?:some|any)\s*(?:where|place|thing)", s):
        return True
    if s in {"not sure", "i dont know", "i don't know", "no idea"}:
        return True
    if _VAGUE_LEADING.match(s):
        return True
    # "someplace …" with extra filler words after stripping tails (e.g. "someplace good")
    if re.match(r"^someplace\b", s) or re.match(r"^somewhere\b", s):
        if len(s.split()) <= 3:
            return True
    return False


def _trim_trailing_stated_at_from_destination(label: str) -> str:
    """
    ``take me to The Face Shop i am at Haldiram`` — the goal is only ``The Face Shop``;
    ``i am at Haldiram`` is the stated start (handled separately).
    """
    s = (label or "").strip()
    if not s:
        return s
    s2 = re.sub(r"\s+(?:i['’]m|i am)\s+at\s+.+$", "", s, flags=re.I | re.S).strip()
    return s2 if s2 else s


def _extract_trailing_i_am_at_place(msg: str) -> Optional[str]:
    """``… take me to X i am at haldiram`` — start is the trailing ``at`` clause."""
    raw = (msg or "").strip()
    if not raw:
        return None
    m = re.search(r"\b(?:i['’]m|i am)\s+at\s+(.+?)\s*$", raw, re.I | re.S)
    if not m:
        return None
    place = m.group(1).strip().rstrip(".,;:!?")
    return place if len(place) >= 2 else None


# -------------------------------
# 3. Destination Resolution
# -------------------------------
def _resolve_destination(msg: str, context: Dict[str, Any]) -> Optional[str]:
    """
    Resolve destination from message or context.

    CASE A: "navigate" alone → use context["selected"]
    CASE B: "navigate to gate b12" → extract from message
    CASE C: "navigate to option 2" → use context["last_results"][index]
    """
    m = msg.lower().strip()

    # CASE C: "option N" or "navigate to option N"
    option_match = re.search(r"option\s+(\d+)", m)
    if option_match:
        idx = int(option_match.group(1)) - 1  # 1-indexed → 0-indexed
        last_results = context.get("last_results", [])
        if 0 <= idx < len(last_results):
            result = last_results[idx]
            return result.get("name") or result.get("location", "")
        return None

    # CASE B: "… to <destination>" (last clause wins when multiple)
    dest_patterns = [
        r"(?:i['’]m|i am)\s+here\b(?:\s+and\s+|\s*,\s*)?\s*(?:i\s+)?(?:want|need)\s+to\s+(?:get\s+to|go\s+to)\s+(.+)",
        r"(?:i['’]m|i am)\s+here\b\s+and\s+(?:i\s+)?(?:want|need)\s+to\s+go\s+to\s+(.+)",
        r"want\s+to\s+go\s+to\s+(.+)",
        r"need\s+to\s+(?:get\s+to|go\s+to)\s+(.+)",
        r"(?:head|heading)\s+(?:to|toward)\s+(.+)",
        r"going\s+to\s+(.+)",
        r"navigate\s+to\s+(.+)",
        r"take\s+me\s+to\s+(.+)",
        r"directions\s+to\s+(.+)",
        r"route\s+to\s+(.+)",
        r"how\s+do\s+i\s+go\s+to\s+(.+)",
        r"how\s+do\s+i\s+get\s+to\s+(.+)",
        r"how\s+to\s+(?:get|go)\s+to\s+(.+)",
        r"walk\s+me\s+to\s+(.+)",
        r"guide\s+me\s+to\s+(.+)",
        r"redirect\s+(?:me\s+)?to\s+(.+)",
        r"show\s+me\s+the\s+way\s+to\s+(.+)",
        r"path\s+to\s+(.+)",
        r"way\s+to\s+(.+)",
        r"(?:get|bring|lead)\s+me\s+to\s+(.+)",
        r"(?:point|send)\s+me\s+to\s+(.+)",
        r"(?:could|can)\s+you\s+(?:help\s+me\s+)?(?:get|bring)\s+(?:me\s+)?to\s+(.+)",
        r"(?:i['’]d|i would)\s+like\s+to\s+(?:get\s+to|go\s+to)\s+(.+)",
        r"\bgo\s+to\s+(.+)",
        r"where\s+(?:is|are)\s+(.+)",
        r"where\s+can\s+i\s+(?:get|find|buy)\s+(?:a|an|some)?\s*(.+)$",
        r"where\s+do\s+i\s+(?:get|find)\s+(?:a|an|some)?\s*(.+)$",
        # Dish / craving → resolved to a shop graph node via ``craving_shop_resolver`` + CSV
        r"(?:i\s+)?(?:want|would like|need)\s+to\s+(?:eat|have|grab|get)\s+(?:a|an|some)?\s*(.+)$",
        r"\b(?:craving|feel\s+like)\s+(?:a|an|some)?\s*(.+)$",
        r"(?:i\s*'?m|i am)\s+hungry(?:\s+for)?\s+(?:a|an|some)?\s*(.+)$",
        r"(?:i\s+)?(?:fancy|could\s+do\s+with)\s+(?:a|an|some)?\s*(.+)$",
        r"(?:get|grab)\s+me\s+(?:a|an|some)?\s*(.+)$",
        r"(?:i\s+)?(?:need|want)\s+(?:a|an|some)\s+(.+)$",
    ]
    for pattern in dest_patterns:
        match = re.search(pattern, m)
        if match:
            dest = match.group(1).strip().strip("\"'").rstrip("?.! ")
            return _trim_trailing_stated_at_from_destination(dest)

    # CASE A: bare "navigate" / "directions" → use context["selected"]
    selected = context.get("selected")
    if selected:
        raw = selected.get("name") or selected.get("location", "")
        return _trim_trailing_stated_at_from_destination(str(raw).strip()) if raw else None

    return None


# Ends the "near <place>" span when a goal phrase follows (not only "and want …").
_NEAR_THEN_GOAL = (
    r"(?:\s*,\s*"
    r"|\s+and\s+(?:i\s+)?(?:want|need|would like|trying)\s+to\s+go\s+to\s+"
    r"|\s+and\s+(?:i\s+)?(?:want|need|would like|trying)\b"
    r"|\s+take\s+me\s+to\s+"
    r"|\s+navigate\s+to\s+"
    r"|\s+walk\s+me\s+to\s+"
    r"|\s+guide\s+me\s+to\s+"
    r"|\s+want\s+to\s+go\s+to\s+"
    r"|\s+going\s+to\s+"
    r"|\s+need\s+to\s+(?:get\s+to|go\s+to)\s+"
    r"|\s+(?:get|bring|lead)\s+me\s+to\s+"
    r"|\s+go\s+to\s+"
    r")"
)


# Phrases that look like ``i am X`` but are not a stated location before ``take me to``.
_I_AM_NOT_A_PLACE = frozenset(
    {
        "here",
        "there",
        "ok",
        "okay",
        "trying",
        "looking",
        "hoping",
        "wondering",
        "not sure",
        "unsure",
        "good",
        "fine",
        "lost",
        "confused",
        "stuck",
        "waiting",
    }
)


def _extract_stated_start_place_from_message(msg: str) -> Optional[str]:
    """
    Extract where the user says they are, before a goal clause:

    - ``I am near …`` / leading ``near …``
    - ``I'm at …`` / ``I am at …``
    - ``I am <shop or place>`` (e.g. ``i am lenskart take me to …``) — not ``i am near …``
    """
    raw = (msg or "").strip()
    if not raw:
        return None
    pat1 = re.compile(
        r"(?:i['’]m|i am)\s+near\s+(.+?)" + _NEAR_THEN_GOAL,
        re.I | re.S,
    )
    mm = pat1.search(raw)
    if mm:
        return mm.group(1).strip().rstrip(".,;:")
    pat2 = re.compile(r"(?:^|\s)near\s+(.+?)" + _NEAR_THEN_GOAL, re.I | re.S)
    mm = pat2.search(raw)
    if mm:
        frag = mm.group(1).strip().rstrip(".,;:")
        low = frag.lower()
        if low.startswith(("the ", "a ", "an ")):
            parts = frag.split(None, 1)
            frag = parts[1] if len(parts) > 1 else frag
        return frag
    pat_at = re.compile(r"(?:i['’]m|i am)\s+at\s+(.+?)" + _NEAR_THEN_GOAL, re.I | re.S)
    mm = pat_at.search(raw)
    if mm:
        return mm.group(1).strip().rstrip(".,;:")
    pat_iam = re.compile(
        r"(?:i['’]m|i am)\s+(?!near\b|at\b)(.+?)" + _NEAR_THEN_GOAL,
        re.I | re.S,
    )
    mm = pat_iam.search(raw)
    if mm:
        place = mm.group(1).strip().rstrip(".,;:")
        low = place.lower()
        if low in _I_AM_NOT_A_PLACE:
            return None
        if len(place) < 2:
            return None
        return place
    trail = _extract_trailing_i_am_at_place(raw)
    if trail:
        return trail
    return None


# -------------------------------
# 4. Navigation API Call
# -------------------------------
def _call_navigation_api(start: str, end: str) -> Dict[str, Any]:
    """
    Call the navigation service directly (same process).
    Uses get_route which resolves labels → graph nodes → shortest path.
    """
    print(f"[NAV] Calling get_route: start={start}, end={end}")

    return get_route(
        start,
        end,
        local_hour=12,
        busy_terminal=False,
    )


# -------------------------------
# 5. Format Navigation Response
# -------------------------------
def _format_navigation_response(nav_data: Dict[str, Any]) -> str:
    """Convert navigation API output into readable step-by-step directions."""
    if not nav_data.get("ok"):
        hint = nav_data.get("hint", "")
        error = nav_data.get("error", "unknown")
        if hint:
            return f"I couldn't generate a route. {hint}"
        return f"I couldn't generate a route ({error})."

    steps = nav_data.get("steps", [])
    if not steps:
        return "I couldn't generate a route."

    total_time = nav_data.get("total_time_minutes", "?")
    header = f"Here is your route (~{total_time} min walk):\n"
    step_lines = "\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)])

    return header + step_lines


def _navigation_message_with_gate_note(nav_msg: str, resolved_goal: str, nav_data: Dict[str, Any]) -> str:
    base = _format_navigation_response(nav_data)
    from app.services.gate_segregation import advisory_for_gate_context

    note = advisory_for_gate_context(nav_msg, resolved_goal or "")
    if note:
        return f"{base}\n\n{note}"
    return base


def _try_pure_rules_navigation(
    *,
    nav_msg: str,
    is_ptp: bool,
    ptp_a: Optional[str],
    ptp_b: Optional[str],
    user_context: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Point A → point B using only rules, CSV/graph resolution, and prior ``last_results``
    (list picks — not a vector KB search). If anything is missing or unresolved, return
    ``None`` so ``handle_chat`` can use RAG + LLM instead.
    """
    location = (user_context.get("source") or user_context.get("location") or "").strip() or None
    destination_raw: Optional[str] = None

    if is_ptp and ptp_a and ptp_b:
        pf = resolve_place_label_to_graph_node(ptp_a)
        if pf:
            location = pf
        destination_raw = ptp_b
    else:
        stated_start = _extract_stated_start_place_from_message(nav_msg)
        if stated_start:
            start_resolved = resolve_place_label_to_graph_node(stated_start)
            if start_resolved:
                location = start_resolved
        destination_raw = _resolve_destination(nav_msg, user_context)

    if not location or not destination_raw or _is_vague_destination(destination_raw):
        return None

    start_graph = resolve_place_label_to_graph_node(location)
    if not start_graph:
        start_graph, _ = resolve_node_id(_map_to_node(location), role="start")
    start_node = start_graph or _map_to_node(location)
    if not start_graph:
        return None

    snippets = user_context.get("last_results") or None
    goal_graph = resolve_walking_goal_id(
        user_message=nav_msg,
        destination_label=destination_raw,
        rag_snippets=snippets,
        start_graph_id=start_graph,
    )
    if not goal_graph:
        return None

    print(f"[NAV] Rules-only: '{location}' → {start_node} ({start_graph}), goal → {goal_graph}")

    nav_data = _call_navigation_api(start_node, goal_graph)

    end_graph, _ = resolve_node_id(goal_graph, role="goal")
    start_graph = start_graph or start_node
    end_graph = end_graph or goal_graph
    if nav_data.get("ok"):
        start_graph = nav_data.get("start_id") or start_graph
        end_graph = nav_data.get("goal_id") or end_graph

    user_context["mode"] = "navigation"

    if nav_data.get("ok"):
        message = _navigation_message_with_gate_note(nav_msg, goal_graph, nav_data)
        return {
            "type": "navigation",
            "intent": "navigation",
            "message": message,
            "data": {
                "navigation": nav_data,
                "start": start_graph,
                "end": end_graph,
            },
            "context": user_context,
        }
    return {
        "type": "navigation",
        "intent": "navigation",
        "message": _navigation_message_with_gate_note(nav_msg, goal_graph, nav_data),
        "data": {
            "navigation": nav_data,
            "start": start_graph,
            "end": end_graph,
        },
        "context": user_context,
    }


# ===============================
# 🔹 MAIN ORCHESTRATOR
# ===============================
async def handle_chat(user_input: str, user_context: Dict[str, Any], language: str = "en") -> Dict[str, Any]:

    if user_context.get("intent") == "time_check":
        flight_reference = _extract_flight_reference(user_input, user_context)
        flight_record = _find_flight_record(flight_reference, user_context)

        if flight_record:
            message, nudges = _build_time_nudges(flight_record)
            enriched_context = dict(user_context)
            if flight_reference:
                enriched_context["flight_number"] = flight_reference
            if flight_record.get("boarding_time"):
                enriched_context["boarding_time"] = flight_record.get("boarding_time")
            if flight_record.get("departure_time"):
                enriched_context["departure_time"] = flight_record.get("departure_time")

            return {
                "type": "flight",
                "intent": "time_check",
                "message": message,
                "data": {"flight": flight_record, "nudges": nudges},
                "context": enriched_context,
            }

    loc_msg = prepare_for_locate_and_context(user_input)
    nav_msg = compose_navigation_message(user_input)

    # STEP 1: Locate (filler-stripped so "Man, take me…" still maps)
    extracted = locate_from_query(loc_msg)

    # STEP 2: Context Engine
    ctx_output = update_context(user_context, extracted, loc_msg)
    user_context = normalize_chat_context(ctx_output["context"])

    # Safety / assistance (medical, lost property, disoriented) — rules + map, no RAG.
    crisis = try_special_assistance_response(loc_msg=loc_msg, user_context=user_context)
    if crisis is not None:
        return crisis

    ptp_a, ptp_b = _parse_place_to_place(nav_msg)
    is_ptp = _is_place_to_place_request(nav_msg) and bool(ptp_a and ptp_b)

    # Clarification — but do not block walking requests: locate/context often omit
    # ``destination``/``intent`` for "take me to BIBA" while _resolve_destination still has the goal.
    if ctx_output["needs_clarification"] and not _is_navigation_request(nav_msg) and not is_ptp:
        return {
            "type": "clarification",
            "intent": None,
            "message": ctx_output["clarification_message"],
            "data": {"navigation": None, "recommendations": None},
            "context": user_context,
        }

    # ===============================
    # 🚀 RULES-ONLY A→B MAP (NO RAG / NO KB SEARCH)
    # If source + destination cannot be resolved from rules + prior list picks, fall through
    # to STEP 3 (RAG / ``plan_navigation_from_chat`` / LLM).
    # ===============================
    if _is_navigation_request(nav_msg) or is_ptp:
        print(f"[ORCHESTRATOR] Navigation-shaped query: {user_input!r} → routing: {nav_msg!r}")
        pure = _try_pure_rules_navigation(
            nav_msg=nav_msg,
            is_ptp=is_ptp,
            ptp_a=ptp_a,
            ptp_b=ptp_b,
            user_context=user_context,
        )
        if pure is not None:
            return pure

    # ===============================
    # 🔥 STEP 3: SAFE INTENT LOGIC (EXISTING)
    # ===============================
    if _is_followup_query(loc_msg) and user_context.get("intent"):
        intent = user_context.get("intent")
    else:
        intent = detect_intent(loc_msg)

    intent_type = normalize_intent(intent)

    print(f"[ORCHESTRATOR] INTENT: {intent}")
    print(f"[ORCHESTRATOR] INTENT_TYPE: {intent_type}")

    location = (user_context.get("source") or user_context.get("location") or "").strip() or None
    destination = user_context.get("destination")
    if isinstance(destination, str) and destination.strip().lower() in SERVICE_LABELS:
        destination = None

    rag_location = _extract_terminal_for_rag(location)

    nav_data = None
    rag_data = None

    # -------------------------------
    # 🔥 SERVICE CALLS
    # -------------------------------
    if destination:
        rag_data = search(
            loc_msg,
            location=None,
            intent="navigation",
            signals=user_context,
        )

        nav_data = plan_navigation_from_chat(
            user_message=loc_msg,
            location_label=location,
            destination_label=destination,
            rag_snippets=rag_data,
        )

    elif intent_type in ["explore", "recommendation"] and intent:
        query = _rewrite_query(loc_msg, user_context)

        print(f"[ORCHESTRATOR] REWRITTEN QUERY: {query}")



        print(f"[ORCHESTRATOR] QUERY: {query}")

        rag_data = search(
            query,
            location=rag_location,
            intent=intent,
            signals=user_context
        )

    print(
        f"[ORCHESTRATOR] RAG: intent_type={intent_type} "
        f"hits={len(rag_data or [])} destination_in_ctx={bool(destination)} "
        f"nav_ok={nav_data.get('ok') if isinstance(nav_data, dict) else None}"
    )

    # -------------------------------
    # 🔥 HARD STOP (NO INTENT = NO RAG)
    # -------------------------------
    if not intent:
        return {
            "type": "general",
            "intent": None,
            "message": "How can I assist you at the airport?",
            "data": {"navigation": None, "recommendations": None},
            "context": user_context,
        }

    # -------------------------------
    # 🔹 RESPONSE ROUTING
    # -------------------------------
    if nav_data and nav_data.get("ok"):
        start_id = nav_data.get("start_id", "")
        goal_id = nav_data.get("goal_id", "")
        return {
            "type": "navigation",
            "intent": intent,
            "message": _navigation_message_with_gate_note(loc_msg, goal_id or "", nav_data),
            "data": {"navigation": nav_data, "recommendations": rag_data, "start": start_id, "end": goal_id},
            "context": user_context,
        }

    if intent_type == "explore" and rag_data:
        return {
            "type": "explore",
            "intent": intent,
            "message": _format_multi_results(rag_data[:3]),
            "data": {"navigation": None, "recommendations": rag_data[:3]},
            "context": user_context,
        }

    if intent_type == "recommendation" and rag_data:
        multi = _is_followup_query(loc_msg)

        message = (
            _format_multi_results(rag_data[:3])
            if multi else _format_single_result(rag_data[0])
        )

        # 🔥 STORE SELECTED RESULT
        user_context["selected"] = rag_data[0]
        user_context["last_results"] = rag_data

        start_raw = (user_context.get("source") or user_context.get("location") or "").strip() or "t2_entrance"
        start_id = resolve_place_label_to_graph_node(start_raw) or None
        if not start_id or start_id not in NODES:
            start_id, _ = resolve_node_id("t2_entrance", role="start")

        sel0 = rag_data[0]
        goal_id = (sel0.get("graph_node_id") or "").strip() or None
        if not goal_id or goal_id not in NODES:
            goal_id = resolve_shop_name_to_graph_node(
                str(sel0.get("name") or ""),
                start_graph_id=start_id,
                avoid_graph_node_id=start_id,
            )
        if not goal_id and start_id:
            goal_id = goal_from_rag_snippets(rag_data, start_id)

        rec_data: Dict[str, Any] = {
            "navigation": nav_data,
            "recommendations": rag_data,
            "selected": rag_data[0],
        }
        if (
            start_id
            and goal_id
            and start_id in NODES
            and goal_id in NODES
            and start_id != goal_id
        ):
            rec_data["start"] = start_id
            rec_data["end"] = goal_id
            rec_data["open_map_after_chat"] = True

        return {
            "type": "recommendation",
            "intent": intent,
            "message": message,
            "data": rec_data,
            "context": user_context,
        }

    # -------------------------------
    # 🔹 FINAL FALLBACK (LLM) — also used when RAG returned 0 hits for recommendation
    # -------------------------------
    rag_empty_hint = ""
    if intent_type == "recommendation" and intent and not rag_data:
        rag_empty_hint = (
            "\nNote: The venue retrieval index returned no matching documents for this query. "
            "Reply helpfully; mention that naming Terminal 2, a cuisine, or a shop type may improve "
            "structured suggestions on the next turn.\n"
        )
        print("[ORCHESTRATOR] RAG returned 0 hits for recommendation → using LLM fallback")

    if intent_type == "explore" and intent and not rag_data:
        rag_empty_hint = (
            "\nNote: Retrieval returned no matching items for this explore query. "
            "Suggest practical airport activities anyway.\n"
        )
        print("[ORCHESTRATOR] RAG returned 0 hits for explore → using LLM fallback")

    if destination and isinstance(nav_data, dict) and not nav_data.get("ok"):
        rag_empty_hint += (
            "\nNote: The user wanted walking directions but the map/router could not complete a path. "
            "Give concise guidance; suggest a clearer landmark or gate if needed.\n"
        )
        print("[ORCHESTRATOR] RAG+router did not return ok navigation → using LLM fallback")

    print("[ORCHESTRATOR] Calling LLM (Ollama) final fallback…")

    op_brief = (user_context or {}).get("_operational_brief")
    if isinstance(op_brief, str) and op_brief.strip():
        rag_empty_hint += (
            "\n\nLive airport operator feed (use for gate changes, delays, and notices; "
            "do not invent flights not listed):\n"
            f"{op_brief.strip()}\n"
        )

    response_text = await call_llm(
        f"""
{SYSTEM_PROMPT}
{rag_empty_hint}
USER QUERY: {user_input}
"""
    )

    llm_response_type = "general"
    if intent_type == "recommendation" and intent and not rag_data:
        llm_response_type = "recommendation"

    return {
        "type": llm_response_type,
        "intent": intent,
        "message": response_text,
        "data": {"navigation": None, "recommendations": rag_data if rag_data else None},
        "context": user_context,
    }