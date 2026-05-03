# backend/app/api/chat.py

from fastapi import APIRouter

from app.models.request import ChatRequest
from app.models.response import ChatResponse

from app.services.orchestrator import handle_chat
from app.services.context_service import (
    get_user_context,
    update_user_context,
)
from app.core.slang_normalizer import clean_airport_slang

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
    patch = {}
    if request.location:
        patch["location"] = request.location
        context["location"] = request.location
    if request.destination is not None:
        patch["destination"] = request.destination
        context["destination"] = request.destination
    if patch:
        update_user_context(request.user_id, patch)

    # ----------------------------
    # 🔹 Step 2.5: Clean slang from user message
    # ----------------------------
    cleaned_message = clean_airport_slang(request.message)

    # ----------------------------
    # 🔹 Step 3: Call orchestrator
    # ----------------------------
    result = await handle_chat(
        user_input=cleaned_message,
        user_context=context,
        language=request.language or "en",
    )

    # ----------------------------
    # 🔹 Step 4: Persist updated context
    # ----------------------------
    update_user_context(request.user_id, result.get("context", {}))

    # ----------------------------
    # 🔹 Step 5: Return response
    # ----------------------------
    return ChatResponse(**result)