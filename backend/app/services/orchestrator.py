# backend/app/services/orchestrator.py

import json
import re
from typing import Any, Dict, List, Optional

from app.services.llm_service import call_llm
from app.services.navigation_service import plan_navigation_from_chat
from app.services.rag_service import search
from app.services.locating_engine import locate_from_query
from app.services.context_engine import update_context
from app.core.llm.prompts import SYSTEM_PROMPT


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
        "time", "late", "delay"
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