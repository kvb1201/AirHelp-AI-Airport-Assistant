# backend/app/services/orchestrator.py

import json
from typing import Any, Dict

from app.services.llm_service import call_llm
from app.services.navigation_service import plan_navigation_from_chat
from app.services.rag_service import search
from app.core.llm.prompts import SYSTEM_PROMPT


def detect_intent(message: str) -> str:
    msg = message.lower()

    if any(word in msg for word in ["gate", "navigate", "direction", "reach", "walk", "how do i get", "where is"]):
        return "navigation"

    if any(word in msg for word in ["food", "eat", "coffee", "restaurant"]):
        return "recommendation"

    if any(word in msg for word in ["time", "late", "delay"]):
        return "time_check"

    return "general"


async def handle_chat(
    user_input: str,
    user_context: Dict[str, Any],
) -> Dict[str, Any]:

    intent = detect_intent(user_input)

    location = user_context.get("location") or "entrance"
    destination = user_context.get("destination")

    nav_data = None
    rag_data = None

    if intent == "navigation":
        rag_data = search(user_input)
        nav_data = plan_navigation_from_chat(
            user_message=user_input,
            location_label=location,
            destination_label=destination,
            rag_snippets=rag_data if rag_data else None,
        )

    elif intent == "recommendation":
        rag_data = search(user_input)

    nav_block = json.dumps(nav_data, indent=2) if nav_data is not None else "null"
    rag_block = json.dumps(rag_data, indent=2) if rag_data is not None else "null"

    prompt = f"""
{SYSTEM_PROMPT}

USER CONTEXT:
Location: {location}
Destination: {destination}

NAVIGATION DATA (graph-computed; use only if ok is true):
{nav_block}

RETRIEVAL / OPTIONS:
{rag_block}

USER QUERY:
{user_input}
"""

    response_text = await call_llm(prompt)

    updated_context = dict(user_context)
    if location:
        updated_context["location"] = location
    if destination:
        updated_context["destination"] = destination

    if nav_data and nav_data.get("ok"):
        updated_context["last_route"] = nav_data
        if nav_data.get("goal_id"):
            updated_context["destination"] = nav_data["goal_id"]

    if rag_data:
        updated_context["last_recommendations"] = rag_data

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
