# backend/app/services/orchestrator.py

import json
from typing import Any, Dict

from app.services.llm_service import call_llm
from app.services.navigation_service import plan_navigation_from_chat
from app.services.rag_service import search
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

    if any(word in msg for word in [
        "food", "eat", "coffee", "restaurant"
    ]):
        return "recommendation"

    if any(word in msg for word in [
        "time", "late", "delay"
    ]):
        return "time_check"

    return "general"


# -------------------------------
# 🔹 Format RAG Response Safely
# -------------------------------
def _format_rag_response(top: Dict[str, Any]) -> str:
    name = top.get("name") or "A place"
    location = top.get("location")

    if location:
        message = f"{name} is located at {location}."
    else:
        message = f"{name} is available."

    if top.get("description"):
        message += f" {top.get('description')}"

    return message


# -------------------------------
# 🔹 Format Navigation Response
# -------------------------------
def _format_navigation(nav_data: Dict[str, Any]) -> str:
    steps = nav_data.get("steps", [])

    if not steps:
        return "I couldn't generate a route."

    return "Here is your route:\n" + "\n".join(
        [f"{i+1}. {step}" for i, step in enumerate(steps)]
    )


# -------------------------------
# 🔹 Main Orchestrator
# -------------------------------
async def handle_chat(
    user_input: str,
    user_context: Dict[str, Any],
) -> Dict[str, Any]:

    intent = detect_intent(user_input)

    location = user_context.get("location") or "entrance"
    destination = user_context.get("destination")

    nav_data = None
    rag_data = None

    # -------------------------------
    # 🔹 Service Calls
    # -------------------------------
    if intent == "navigation":
        rag_data = search(user_input, location)

        nav_data = plan_navigation_from_chat(
            user_message=user_input,
            location_label=location,
            destination_label=destination,
            rag_snippets=rag_data if rag_data else None,
        )

    elif intent == "recommendation":
        rag_data = search(user_input, location)

    # -------------------------------
    # 🔥 1. Deterministic Navigation
    # -------------------------------
    if nav_data and nav_data.get("ok"):
        message = _format_navigation(nav_data)

        return {
            "type": "navigation",
            "intent": "navigation",
            "message": message,
            "data": {
                "navigation": nav_data,
                "recommendations": rag_data,
            },
            "context": {
                **user_context,
                "location": location,
                "destination": nav_data.get("goal_id"),
                "last_route": nav_data,
            },
        }

    # -------------------------------
    # 🔥 2. Deterministic RAG (CRITICAL)
    # -------------------------------
    if intent == "recommendation" and rag_data:
        message = _format_rag_response(rag_data[0])

        return {
            "type": "recommendation",
            "intent": "recommendation",
            "message": message,
            "data": {
                "navigation": nav_data,
                "recommendations": rag_data,
            },
            "context": {
                **user_context,
                "location": location,
                "last_recommendations": rag_data,
            },
        }

    # -------------------------------
    # 🔹 LLM Fallback (ONLY when needed)
    # -------------------------------
    nav_block = json.dumps(nav_data, indent=2) if nav_data else "None"
    rag_block = json.dumps(rag_data, indent=2) if rag_data else "None"

    prompt = f"""
{SYSTEM_PROMPT}

USER LOCATION:
{location}

AVAILABLE OPTIONS:
{rag_block}

NAVIGATION DATA:
{nav_block}

USER QUERY:
{user_input}
"""

    response_text = await call_llm(prompt)

    # -------------------------------
    # 🔹 Context Update
    # -------------------------------
    updated_context = dict(user_context)

    updated_context["location"] = location

    if destination:
        updated_context["destination"] = destination

    if rag_data:
        updated_context["last_recommendations"] = rag_data

    # -------------------------------
    # 🔹 Final Response
    # -------------------------------
    return {
        "type": intent,
        "intent": intent,
        "message": response_text,
        "data": {
            "navigation": nav_data,
            "recommendations": rag_data,
        },
        "context": updated_context,
    }