# backend/app/services/orchestrator.py

from typing import Dict, Any

from app.services.llm_service import call_llm

# NOTE:
# These will be replaced with real implementations later
# Keep imports ready for easy swap
# from app.services.navigation_service import get_route
# from app.services.rag_service import search


# -------------------------------
# 🔹 Intent Detection (Simple + Fast)
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
# 🔹 Main Orchestrator Function
# -------------------------------
async def handle_chat(
    user_input: str,
    user_context: Dict[str, Any]
) -> Dict[str, Any]:

    intent = detect_intent(user_input)

    # ----------------------------------
    # 🔹 MOCK DATA (Replace Later)
    # ----------------------------------
    nav_data = None
    rag_data = None

    if intent == "navigation":
        nav_data = {
            "path": ["security", "corridor_A", "gate_B12"],
            "total_time": 6,
            "steps": [
                "Walk straight from security",
                "Enter Corridor A",
                "Continue to Gate B12"
            ]
        }

    elif intent == "recommendation":
        rag_data = [
            {
                "name": "Cafe A",
                "distance": "2 min",
                "time_required": 5,
                "price_range": "low"
            },
            {
                "name": "Snack Bar B",
                "distance": "3 min",
                "time_required": 4,
                "price_range": "medium"
            }
        ]

    # ----------------------------------
    # 🔹 Extract Context
    # ----------------------------------
    location = user_context.get("location", "unknown")
    destination = user_context.get("destination", None)

    # ----------------------------------
    # 🔹 Build Controlled Prompt
    # ----------------------------------
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

FOOD / SHOP DATA:
{rag_data}

USER QUERY:
{user_input}

Provide a helpful, concise response.
"""

    # ----------------------------------
    # 🔹 Call LLM
    # ----------------------------------
    response_text = await call_llm(prompt)

    # ----------------------------------
    # 🔹 Update Context (Minimal)
    # ----------------------------------
    updated_context = dict(user_context)

    if intent == "navigation":
        updated_context["destination"] = "gate_B12"  # replace with parsed later

    if location:
        updated_context["location"] = location

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