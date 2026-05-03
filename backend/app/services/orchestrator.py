# backend/app/services/orchestrator.py

import json
from typing import Any, Dict

from app.services.llm_service import call_llm
from app.services.navigation_service import plan_navigation_from_chat
from app.services.rag_service import search
from app.core.llm.prompts import SYSTEM_PROMPT


# -------------------------------
# 🔹 Intent Detection (keep simple)
# -------------------------------
def detect_intent(message: str) -> str:
    msg = message.lower()

    if any(word in msg for word in ["gate", "navigate", "direction", "reach", "walk", "how do i get", "where is"]):
        return "navigation"

    if any(word in msg for word in ["food", "eat", "coffee", "restaurant"]):
        return "recommendation"

    if any(word in msg for word in ["time", "late", "delay"]):
        return "time_check"

    return "general"


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
    # 🔥 Deterministic Fallback (IMPORTANT)
    # -------------------------------
    if nav_data and nav_data.get("ok"):
        steps = nav_data.get("steps", [])
        message = "Here is your route:\n" + "\n".join(
            [f"{i+1}. {step}" for i, step in enumerate(steps)]
        )

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
    # 🔹 Build Better Prompt
    # -------------------------------
    nav_block = json.dumps(nav_data, indent=2) if nav_data else "None"
    rag_block = json.dumps(rag_data, indent=2) if rag_data else "None"

    prompt = f"""
{SYSTEM_PROMPT}

CURRENT USER STATE:
- Location: {location}
- Destination: {destination}

AVAILABLE OPTIONS (ONLY USE THESE):
{rag_block}

NAVIGATION PLAN (ONLY USE IF ok=true):
{nav_block}

USER QUERY:
{user_input}

Instructions:
- Do NOT invent places
- Prefer nearby options
- If navigation exists, guide step-by-step
- Keep answer concise
"""

    # -------------------------------
    # 🔹 LLM Call
    # -------------------------------
    response_text = await call_llm(prompt)

    # -------------------------------
    # 🔹 Context Update
    # -------------------------------
    updated_context = dict(user_context)

    updated_context["location"] = location

    if destination:
        updated_context["destination"] = destination

    if nav_data and nav_data.get("ok"):
        updated_context["last_route"] = nav_data
        updated_context["destination"] = nav_data.get("goal_id")

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