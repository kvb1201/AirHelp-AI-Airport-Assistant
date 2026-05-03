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


# -------------------------------
# 🔹 MAIN ORCHESTRATOR
# -------------------------------
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

    # -------------------------------
    # 🔥 STEP 3: SAFE INTENT LOGIC (FIXED)
    # -------------------------------
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
        return {
            "type": "navigation",
            "intent": intent,
            "message": _format_navigation(nav_data),
            "data": {"navigation": nav_data, "recommendations": rag_data},
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

        return {
            "type": "recommendation",
            "intent": intent,
            "message": message,
            "data": {"navigation": nav_data, "recommendations": rag_data},
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