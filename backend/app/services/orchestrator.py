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
# 🔥 Query Rewriting (CRITICAL FIX)
# -------------------------------
def _rewrite_query(user_input: str, intent: str, location: Optional[str]) -> Optional[str]:
    msg = user_input.lower()

    if _is_followup_query(msg):
        if intent and location:
            return f"{intent} options in {location}"
        elif intent:
            return f"{intent} options"

    return None


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
# 🔹 Format Explore
# -------------------------------
def _format_explore_response(results: List[Dict], location: Optional[str]) -> str:
    header = location.replace("_", " ").title() if location else "your area"

    lines = [f"Here are some things to do near {header}:\n"]

    for r in results:
        line = f"• {r.get('name')}"
        if r.get("location"):
            line += f" ({r['location']})"
        lines.append(line)

    return "\n".join(lines)


# -------------------------------
# 🔹 MAIN ORCHESTRATOR
# -------------------------------
async def handle_chat(user_input: str, user_context: Dict[str, Any]) -> Dict[str, Any]:

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

    # STEP 3: Intent
    if _is_followup_query(user_input):
        intent = user_context.get("intent")
    else:
        intent = user_context.get("intent") or detect_intent(user_input)

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

    elif intent_type in ["explore", "recommendation"]:

        # 🔥 FIX: Query rewriting
        rewritten = _rewrite_query(user_input, intent, rag_location)

        if rewritten:
            print(f"[ORCHESTRATOR] REWRITTEN QUERY: {rewritten}")
            query = rewritten
        else:
            query = _build_search_query(user_input, rag_location, intent_type)

        print(f"[ORCHESTRATOR] CALLING RAG with query: {query}")
        print(f"[ORCHESTRATOR] Original intent passed to RAG: {intent}")

        rag_data = search(
            query,
            location=rag_location,
            intent=intent,
            signals=user_context
        )

    # -------------------------------
    # 🔥 RESPONSE ROUTING
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
            "message": _format_explore_response(rag_data[:3], rag_location),
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

        multi = _is_followup_query(user_input) or any(x in user_input.lower() for x in [
            "nearest", "nearby", "options", "list", "all",
            "restaurants", "lounges", "shops"
        ])

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
    # 🔹 Fallback
    # -------------------------------
    if ctx_output.get("fallback"):
        return {
            "type": "fallback",
            "intent": intent or "general",
            "message": "I couldn't determine your location. Here are some general options.",
            "data": {"navigation": None, "recommendations": rag_data},
            "context": user_context,
        }

    # -------------------------------
    # 🔹 LLM fallback
    # -------------------------------
    response_text = await call_llm(f"""
{SYSTEM_PROMPT}

USER QUERY: {user_input}

AVAILABLE OPTIONS:
{json.dumps(rag_data, indent=2) if rag_data else "None"}
""")

    return {
        "type": intent or "general",
        "intent": intent or "general",
        "message": response_text,
        "data": {"navigation": nav_data, "recommendations": rag_data},
        "context": user_context,
    }