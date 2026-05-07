# backend/app/api/chat.py

from fastapi import APIRouter, UploadFile, File, Form

from app.models.request import ChatRequest
from app.models.response import ChatResponse

from app.services.orchestrator import handle_chat
from app.services.context_service import (
    get_user_context,
    update_user_context,
)
from app.core.slang_normalizer import clean_airport_slang
from app.core.language_router import route_input

from app.services import operational_state_service as ops_state
import tempfile
import os

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint with smart language routing.

    Pipeline:
    1. Language Router detects language & routes:
       - English (voice/text) → direct to orchestrator
       - Hinglish (typed)     → slang map → orchestrator
       - Other language        → translate to English → orchestrator
    2. Fetch user context
    3. Update context with incoming data
    4. Pass cleaned English text to orchestrator
    5. Return structured response
    """

    # ----------------------------
    # 🔹 Step 1: Language Routing
    # ----------------------------
    route_result = route_input(
        text=request.message,
        input_mode=request.input_mode,
        whisper_lang=request.whisper_lang,
    )
    
    routed_message = route_result["english_text"]
    pipeline_used = route_result["pipeline"]
    detected_lang = route_result["detected_lang"]
    
    print(f"🌐 Language Router: detected={detected_lang}, pipeline={pipeline_used}")
    print(f"   Original: {request.message[:80]}")
    print(f"   Routed:   {routed_message[:80]}")

    # ----------------------------
    # 🔹 Step 2: Get existing context
    # ----------------------------
    context = get_user_context(request.user_id) or {}
    brief = ops_state.get_brief_for_llm()
    if brief:
        context = {**context, "_operational_brief": brief}

    # ----------------------------
    # 🔹 Step 3: Update context (location etc.)
    # ----------------------------
    patch = {}
    if request.location:
        patch["location"] = request.location
        patch["source"] = request.location
        context["location"] = request.location
        context["source"] = request.location
    if request.destination is not None:
        patch["destination"] = request.destination
        context["destination"] = request.destination
    if request.flight_number:
        patch["flight_number"] = request.flight_number
        context["flight_number"] = request.flight_number
    if request.boarding_time:
        patch["boarding_time"] = request.boarding_time
        context["boarding_time"] = request.boarding_time
    if request.departure_time:
        patch["departure_time"] = request.departure_time
        context["departure_time"] = request.departure_time
    if patch:
        update_user_context(request.user_id, patch)

    # ----------------------------
    # 🔹 Step 4: Apply slang cleaning (for English / already-routed text)
    # ----------------------------
    # For "direct" pipeline (English), still run slang cleaner for typo fixes
    # For "slang_map" pipeline, already cleaned by language_router
    # For "translation" pipeline, already translated to English
    if pipeline_used == "direct":
        cleaned_message = clean_airport_slang(routed_message)
    else:
        cleaned_message = routed_message

    # ----------------------------
    # 🔹 Step 5: Call orchestrator (always receives English)
    # ----------------------------
    result = await handle_chat(
        user_input=cleaned_message,
        user_context=context,
        language="en",  # Always English after routing
    )

    # Add language routing metadata to response
    result.setdefault("data", {})
    if isinstance(result["data"], dict):
        result["data"]["language_routing"] = {
            "detected_lang": detected_lang,
            "pipeline": pipeline_used,
            "original_text": route_result["original_text"],
        }

    # ----------------------------
    # 🔹 Step 6: Persist updated context
    # ----------------------------
    update_user_context(request.user_id, result.get("context", {}))

    # ----------------------------
    # 🔹 Step 7: Return response
    # ----------------------------
    return ChatResponse(**result)


