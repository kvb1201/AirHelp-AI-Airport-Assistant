import json
import re
from typing import Any, Dict, List, Optional

from app.services.llm_service import call_llm
from app.services.navigation_service import plan_navigation_from_chat, get_route
from app.services.rag_service import search
from app.services.locating_engine import locate_from_query
from app.services.context_engine import update_context
from app.core.llm.prompts import SYSTEM_PROMPT


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
        "gate", "navigate", "direction", "reach",
        "walk", "how do i get", "where is"
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
# 🔹 Format Single Result
# -------------------------------
def _format_single_result(r: Dict[str, Any]) -> str:
    name = r.get("name")
    loc = r.get("location", "")
    desc = r.get("description", "")

    lines = []

    if loc:
        lines.append(f"{name} ({loc})")
    else:
        lines.append(name)

    if desc:
        lines.append("\n" + desc[:120])

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
        "route",
        "how do i get to",
        "walk me to",
        "guide me to",
    ]
    return any(t in m for t in triggers)


# -------------------------------
# 2. Node Mapping
# -------------------------------
def _map_to_node(location_str: str) -> str:
    """
    Map human-readable location strings to graph node IDs.
    RAG returns names like 'Gate D3', 'food court', etc.
    The navigation graph uses snake_case IDs.
    """
    if not location_str:
        return "entrance"

    loc = location_str.strip().lower()

    # Direct gate pattern: "gate d3" → "gate_d3", "gate b12" → "gate_b12"
    gate_match = re.match(r"gate\s+([a-z]?\d+)", loc)
    if gate_match:
        return f"gate_{gate_match.group(1)}"

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

    # CASE B: "navigate to <destination>" / "take me to <destination>"
    dest_patterns = [
        r"navigate\s+to\s+(.+)",
        r"take\s+me\s+to\s+(.+)",
        r"directions\s+to\s+(.+)",
        r"route\s+to\s+(.+)",
        r"how\s+do\s+i\s+go\s+to\s+(.+)",
        r"how\s+do\s+i\s+get\s+to\s+(.+)",
        r"walk\s+me\s+to\s+(.+)",
        r"guide\s+me\s+to\s+(.+)",
    ]
    for pattern in dest_patterns:
        match = re.search(pattern, m)
        if match:
            return match.group(1).strip()

    # CASE A: bare "navigate" / "directions" → use context["selected"]
    selected = context.get("selected")
    if selected:
        return selected.get("name") or selected.get("location", "")

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


# ===============================
# 🔹 MAIN ORCHESTRATOR
# ===============================
async def handle_chat(user_input: str, user_context: Dict[str, Any], language: str = "en") -> Dict[str, Any]:

    # STEP 1: Locate
    extracted = locate_from_query(user_input)

    # STEP 2: Context Engine
    ctx_output = update_context(user_context, extracted, user_input)
    user_context = ctx_output["context"]

    # Clarification
    if ctx_output["needs_clarification"]:
        return {
            "type": "clarification",
            "intent": None,
            "message": ctx_output["clarification_message"],
            "data": {"navigation": None, "recommendations": None},
            "context": user_context,
        }

    # ===============================
    # 🚀 NAVIGATION INTERCEPT (BEFORE RAG)
    # ===============================
    if _is_navigation_request(user_input):
        print(f"[ORCHESTRATOR] Navigation request detected: {user_input}")

        location = user_context.get("source")
        destination_raw = _resolve_destination(user_input, user_context)

        # --- Validate source ---
        if not location:
            return {
                "type": "clarification",
                "intent": "navigation",
                "message": "Where are you currently?",
                "data": {"navigation": None, "recommendations": None},
                "context": user_context,
            }

        # --- Validate destination ---
        if not destination_raw:
            return {
                "type": "clarification",
                "intent": "navigation",
                "message": "Where would you like to go?",
                "data": {"navigation": None, "recommendations": None},
                "context": user_context,
            }

        # --- Map to node IDs ---
        start_node = _map_to_node(location)
        end_node = _map_to_node(destination_raw)

        print(f"[NAV] Resolved: '{location}' → {start_node}, '{destination_raw}' → {end_node}")

        # --- Call navigation ---
        nav_data = _call_navigation_api(start_node, end_node)

        # --- Update context ---
        user_context["mode"] = "navigation"

        # --- Format response ---
        if nav_data.get("ok"):
            message = _format_navigation_response(nav_data)
            return {
                "type": "navigation",
                "intent": "navigation",
                "message": message,
                "data": {"navigation": nav_data, "start": start_node, "end": end_node},
                "context": user_context,
            }
        else:
            return {
                "type": "navigation",
                "intent": "navigation",
                "message": _format_navigation_response(nav_data),
                "data": {"navigation": nav_data, "start": start_node, "end": end_node},
                "context": user_context,
            }

    # ===============================
    # 🔥 STEP 3: SAFE INTENT LOGIC (EXISTING)
    # ===============================
    if _is_followup_query(user_input) and user_context.get("intent"):
        intent = user_context.get("intent")
    else:
        intent = detect_intent(user_input)

    intent_type = normalize_intent(intent)

    print(f"[ORCHESTRATOR] INTENT: {intent}")
    print(f"[ORCHESTRATOR] INTENT_TYPE: {intent_type}")

    location = user_context.get("source")
    destination = user_context.get("destination")

    rag_location = _extract_terminal_for_rag(location)

    nav_data = None
    rag_data = None

    # -------------------------------
    # 🔥 SERVICE CALLS
    # -------------------------------
    if destination:
        rag_data = search(
            user_input,
            location=None,
            intent="navigation",
            signals=user_context
        )

        nav_data = plan_navigation_from_chat(
            user_message=user_input,
            location_label=location,
            destination_label=destination,
            rag_snippets=rag_data,
        )

    elif intent_type in ["explore", "recommendation"] and intent:
        query = _rewrite_query(user_input, user_context)

        print(f"[ORCHESTRATOR] REWRITTEN QUERY: {query}")



        print(f"[ORCHESTRATOR] QUERY: {query}")

        rag_data = search(
            query,
            location=rag_location,
            intent=intent,
            signals=user_context
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
            "message": _format_navigation(nav_data),
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

    if intent_type == "recommendation":
        if not rag_data:
            return {
                "type": "recommendation",
                "intent": intent,
                "message": "I couldn't find relevant options.",
                "data": {"navigation": None, "recommendations": []},
                "context": user_context,
            }

        multi = _is_followup_query(user_input)

        message = (
            _format_multi_results(rag_data[:3])
            if multi else _format_single_result(rag_data[0])
        )

        # 🔥 STORE SELECTED RESULT
        if rag_data:
            user_context["selected"] = rag_data[0]
            user_context["last_results"] = rag_data

        return {
            "type": "recommendation",
            "intent": intent,
            "message": message,
            "data": {
                "navigation": nav_data,
                "recommendations": rag_data,
                "selected": rag_data[0] if rag_data else None   # 👈 IMPORTANT
            },
            "context": user_context,
        }

    # -------------------------------
    # 🔹 FINAL FALLBACK
    # -------------------------------
    response_text = await call_llm(
        f"""
{SYSTEM_PROMPT}

USER QUERY: {user_input}
"""
    )

    return {
        "type": "general",
        "intent": intent,
        "message": response_text,
        "data": {"navigation": None, "recommendations": None},
        "context": user_context,
    }