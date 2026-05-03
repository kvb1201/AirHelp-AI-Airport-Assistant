# backend/app/services/orchestrator.py

from typing import Dict, Any

from app.services.llm_service import call_llm
from app.services.navigation_service import get_route
from app.services.rag_service import search
from app.core.llm.prompts import SYSTEM_PROMPT


# -------------------------------
# 🔹 Intent Detection
# -------------------------------
def detect_intent(message: str) -> str:
    msg = message.lower()

    if any(word in msg for word in ["gate", "navigate", "direction", "reach"]):
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
    user_context: Dict[str, Any]
) -> Dict[str, Any]:

    intent = detect_intent(user_input)

    # ----------------------------------
    # 🔹 Extract Context
    # ----------------------------------
    location = user_context.get("location", "unknown")
    destination = user_context.get("destination")

    # ----------------------------------
    # 🔹 Call Services (Mock/Real)
    # ----------------------------------
    nav_data = None
    rag_data = None

    if intent == "navigation":
        nav_data = get_route(location, user_input)

    elif intent == "recommendation":
        rag_data = search(user_input)

    # ----------------------------------
    # 🔹 Build Prompt using SYSTEM_PROMPT
    # ----------------------------------
    prompt = f"""
{SYSTEM_PROMPT}

USER CONTEXT:
Location: {location}
Destination: {destination}

NAVIGATION DATA:
{nav_data}

AVAILABLE OPTIONS:
{rag_data}

USER QUERY:
{user_input}
"""

    # ----------------------------------
    # 🔹 Call LLM
    # ----------------------------------
    response_text = await call_llm(prompt)

    # ----------------------------------
    # 🔹 Update Context
    # ----------------------------------
    updated_context = dict(user_context)

    if location:
        updated_context["location"] = location

    if nav_data:
        updated_context["last_route"] = nav_data

    if rag_data:
        updated_context["last_recommendations"] = rag_data

    # (Optional improvement later: parse destination from query)

    # ----------------------------------
    # 🔹 Final Response
    # ----------------------------------
    return {
        "type": intent,
        "intent": intent,
        "message": response_text,

        "data": {
            "navigation": nav_data,
            "recommendations": rag_data
        },

        "context": updated_context
    }