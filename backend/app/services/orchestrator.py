# backend/app/services/orchestrator.py

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.llm_service import call_llm
from app.services.navigation_service import plan_navigation_from_chat
from app.services.rag_service import search
from app.services.locating_engine import locate_from_query
from app.services.context_engine import update_context
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
# 🔹 Intent Detection
# -------------------------------
def detect_intent(message: str) -> str:
    msg = message.lower()

    if any(word in msg for word in [
        "gate", "navigate", "direction", "reach",
        "walk", "how do i get", "where is"
    ]):
        return "navigation"

    if any(phrase in msg for phrase in [
        "what can i do",
        "things to do",
        "explore",
        "nearby",
        "around",
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
# 🔹 Extract Terminal for RAG
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
def _build_search_query(user_input: str, location: Optional[str], intent: str) -> str:

    if intent == "explore":
        return f"things to do in {location} airport" if location else "things to do in airport"

    if intent == "recommendation":
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
def _format_rag_response(top: Dict[str, Any]) -> str:
    name = top.get("name") or "A place"
    loc = top.get("location", "")
    desc = top.get("description", "")

    lines = []

    # Title
    if loc:
        lines.append(f"{name} ({loc})")
    else:
        lines.append(name)

    lines.append("")

    # Extract info
    cuisine = ""
    timings = ""
    price = ""

    if "Cuisine:" in desc:
        cuisine = desc.split("Cuisine:")[1].split(".")[0].strip()

    if "Timings:" in desc:
        timings = desc.split("Timings:")[1].split(".")[0].strip()
    elif "Hours:" in desc:
        timings = desc.split("Hours:")[1].split(".")[0].strip()

    if "Price range:" in desc:
        price = desc.split("Price range:")[1].split(".")[0].strip()

    if cuisine:
        lines.append(f"Cuisine: {cuisine}")

    if timings:
        lines.append(f"Timings: {timings}")

    if price:
        lines.append(f"Price: {price}")

    # Smart hint
    d = desc.lower()

    if "fast" in d or "quick" in d:
        lines.append("\nBest for a quick bite.")
    elif "restaurant" in d or "multi-cuisine" in d:
        lines.append("\nBest for a proper meal.")
    elif "lounge" in d:
        lines.append("\nGood place to relax.")
    elif "coffee" in d or "café" in d:
        lines.append("\nPerfect for coffee.")

    return "\n".join(lines)


# -------------------------------
# 🔹 Format Multiple Results
# -------------------------------
def _format_multi_results(results: List[Dict]) -> str:
    lines = ["Here are some options:\n"]

    for r in results:
        name = r.get("name")
        loc = r.get("location", "")

        line = f"• {name}"
        if loc:
            line += f" ({loc})"

        lines.append(line)

    return "\n".join(lines)


# -------------------------------
# 🔹 Format Explore
# -------------------------------
def _format_explore_response(results: List[Dict], location: Optional[str]) -> str:
    header = location.replace("_", " ").title() if location else "your area"

    lines = [f"Here are some things you can do near {header}:\n"]

    for r in results:
        name = r.get("name")
        loc = r.get("location", "")

        line = f"• {name}"
        if loc:
            line += f" ({loc})"

        lines.append(line)

    return "\n".join(lines)


# -------------------------------
# 🔹 Format Navigation
# -------------------------------
def _format_navigation(nav_data: Dict[str, Any]) -> str:
    steps = nav_data.get("steps", [])
    if not steps:
        return "I couldn't generate a route."

    return "Here is your route:\n" + "\n".join(
        [f"{i+1}. {s}" for i, s in enumerate(steps)]
    )


# -------------------------------
# 🔹 MAIN ORCHESTRATOR
# -------------------------------
async def handle_chat(user_input: str, user_context: Dict[str, Any]) -> Dict[str, Any]:

    extracted = locate_from_query(user_input)
    extracted["raw_query"] = user_input

    user_context = update_context(user_context, extracted)

    intent = detect_intent(user_input)

    if intent == "time_check":
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

    location = extracted.get("location") or user_context.get("location")
    destination = user_context.get("destination")

    rag_location = _extract_terminal_for_rag(location)

    nav_data = None
    rag_data = None

    # -------------------------------
    # 🔹 SERVICE CALLS
    # -------------------------------
    if intent == "navigation":
        rag_data = search(user_input, location=None, intent=intent)

        nav_data = plan_navigation_from_chat(
            user_message=user_input,
            location_label=location,
            destination_label=destination,
            rag_snippets=rag_data,
        )

    elif intent in ["explore", "recommendation"]:
        query = _build_search_query(user_input, rag_location, intent)
        rag_data = search(query, location=rag_location, intent=intent)

    # -------------------------------
    # 🔥 RESPONSE ROUTING
    # -------------------------------
    if nav_data and nav_data.get("ok"):
        return {
            "type": "navigation",
            "intent": "navigation",
            "message": _format_navigation(nav_data),
            "data": {"navigation": nav_data, "recommendations": rag_data},
            "context": {**user_context, "location": location},
        }

    if intent == "explore" and rag_data:
        return {
            "type": "explore",
            "intent": "explore",
            "message": _format_explore_response(rag_data[:3], rag_location),
            "data": {"navigation": None, "recommendations": rag_data[:3]},
            "context": user_context,
        }

    if intent == "recommendation" and rag_data:
        msg_lower = user_input.lower()

        multi = any(x in msg_lower for x in [
            "nearest", "nearby", "options", "list", "all"
        ]) or any(x in msg_lower for x in [
            "restaurants", "lounges", "shops"
        ])

        if multi:
            message = _format_multi_results(rag_data[:3])
        else:
            message = _format_rag_response(rag_data[0])

        return {
            "type": "recommendation",
            "intent": "recommendation",
            "message": message,
            "data": {"navigation": nav_data, "recommendations": rag_data},
            "context": user_context,
        }

    # -------------------------------
    # 🔹 FALLBACK
    # -------------------------------
    response_text = await call_llm(f"""
{SYSTEM_PROMPT}

USER QUERY: {user_input}
AVAILABLE OPTIONS:
{json.dumps(rag_data, indent=2) if rag_data else "None"}
""")

    return {
        "type": intent,
        "intent": intent,
        "message": response_text,
        "data": {"navigation": nav_data, "recommendations": rag_data},
        "context": user_context,
    }