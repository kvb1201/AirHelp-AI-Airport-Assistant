# backend/app/services/orchestrator.py

from typing import Any, Dict

from app.services.llm_service import call_llm
from app.services.rag_service import get_relevant_context


def detect_intent(message: str) -> str:
    """Classify the user's message into one of the current backend flows."""
    msg = message.lower()

    if any(word in msg for word in ["gate", "navigate", "direction", "reach"]):
        return "navigation"

    if any(
        word in msg
        for word in ["food", "eat", "coffee", "restaurant", "shop", "buy", "lounge", "service", "forex"]
    ):
        return "recommendation"

    if any(word in msg for word in ["time", "late", "delay", "flight", "boarding"]):
        return "time_check"

    return "general"


async def handle_chat(user_input: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Route the chat request and ground the prompt in structured airport data."""
    intent = detect_intent(user_input)

    nav_data = None
    rag_data = None
    rag_context = get_relevant_context(user_input)

    if intent == "navigation":
        nav_data = {
            "path": ["security", "corridor_A", "gate_B12"],
            "total_time": 6,
            "steps": [
                "Walk straight from security",
                "Enter Corridor A",
                "Continue to Gate B12",
            ],
        }

    elif intent in {"recommendation", "general", "time_check"}:
        # Recommendation data now comes from the compiled knowledge base instead
        # of hardcoded mock values, so the prompt stays grounded in repo data.
        rag_data = rag_context["places"]

    location = user_context.get("location", "unknown")
    destination = user_context.get("destination", None)

    prompt = f"""
You are an intelligent airport assistant.

STRICT RULES:
- Do NOT make up information
- ONLY use the provided data
- If unsure, say "I don't have that information"

USER CONTEXT:
Location: {location}
Destination: {destination}

NAVIGATION DATA:
{nav_data}

STRUCTURED PLACE DATA:
{rag_data}

RETRIEVED KNOWLEDGE CHUNKS:
{rag_context["chunks"]}

USER QUERY:
{user_input}

Provide a helpful, concise response.
"""

    response_text = await call_llm(prompt)

    updated_context = dict(user_context)
    if intent == "navigation":
        updated_context["destination"] = "gate_B12"
    if location:
        updated_context["location"] = location

    return {
        "type": intent,
        "intent": intent,
        "message": response_text,
        "data": {
            "navigation": nav_data,
            "recommendations": rag_data,
            "knowledge_chunks": rag_context["chunks"],
        },
        "context": updated_context,
    }

