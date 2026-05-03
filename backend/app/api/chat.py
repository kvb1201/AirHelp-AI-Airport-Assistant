# backend/app/api/chat.py

from fastapi import APIRouter

from app.models.request import ChatRequest
from app.models.response import ChatResponse

from app.services.orchestrator import handle_chat
from app.services.context_service import (
    get_user_context,
    update_user_context,
)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint.

    Flow:
    1. Fetch user context
    2. Update context with incoming data
    3. Pass to orchestrator
    4. Return structured response
    """

    # ----------------------------
    # 🔹 Step 1: Get existing context
    # ----------------------------
    context = get_user_context(request.user_id) or {}

    # ----------------------------
    # 🔹 Step 2: Update context (location etc.)
    # ----------------------------
    if request.location:
        update_user_context(request.user_id, {
            "location": request.location
        })
        context["location"] = request.location

    # ----------------------------
    # 🔹 Step 3: Call orchestrator
    # ----------------------------
    result = await handle_chat(
        user_input=request.message,
        user_context=context
    )

    # ----------------------------
    # 🔹 Step 4: Persist updated context
    # ----------------------------
    update_user_context(request.user_id, result.get("context", {}))

    # ----------------------------
    # 🔹 Step 5: Return response
    # ----------------------------
    return ChatResponse(**result)