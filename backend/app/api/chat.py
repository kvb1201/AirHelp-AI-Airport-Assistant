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
from app.services.simple_ocr_service import extract_boarding_pass_simple
import tempfile
import os

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


@router.post("/chat/image", response_model=ChatResponse)
async def chat_with_image_endpoint(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    message: str = Form(""),
    location: str = Form(None),
    destination: str = Form(None),
    language: str = Form("en")
):
    """
    Chat endpoint with image processing for boarding passes.
    
    Process uploaded image (boarding pass) and use extracted information as context.
    """
    if not file.content_type.startswith("image/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid file type, image expected.")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await file.read()
        tmp.write(content)
        image_path = tmp.name
    
    try:
        # Extract boarding pass information
        boarding_pass_info = extract_boarding_pass_simple(image_path)
        
        # Clean up temp file
        os.unlink(image_path)
        
        # Get existing context
        context = get_user_context(user_id) or {}
        
        # Update context with boarding pass information
        if 'error' not in boarding_pass_info:
            context.update({
                'boarding_pass': boarding_pass_info,
                'flight_number': boarding_pass_info.get('flight_number'),
                'from_to': boarding_pass_info.get('from_to'),
                'gate': boarding_pass_info.get('gate'),
                'seat': boarding_pass_info.get('seat'),
                'terminal': boarding_pass_info.get('terminal'),
                'departure_time': boarding_pass_info.get('departure_time'),
                'date': boarding_pass_info.get('date')
            })
        
        # Update location if provided
        if location:
            context["location"] = location
        if destination is not None:
            context["destination"] = destination
        
        # Create enhanced message with boarding pass context
        if 'error' not in boarding_pass_info:
            enhanced_message = f"""
User message: {message}
Boarding pass information:
- Flight: {boarding_pass_info.get('flight_number', 'Unknown')}
- Route: {boarding_pass_info.get('from_to', 'Unknown')}
- Date: {boarding_pass_info.get('date', 'Unknown')}
- Time: {boarding_pass_info.get('departure_time', 'Unknown')}
- Gate: {boarding_pass_info.get('gate', 'Unknown')}
- Seat: {boarding_pass_info.get('seat', 'Unknown')}
- Terminal: {boarding_pass_info.get('terminal', 'Unknown')}
"""
        else:
            enhanced_message = f"User message: {message}\nNote: Boarding pass extraction failed: {boarding_pass_info.get('error', 'Unknown error')}"
        
        # Clean slang from enhanced message
        cleaned_message = clean_airport_slang(enhanced_message)
        
        # Call orchestrator with enhanced context
        result = await handle_chat(
            user_input=cleaned_message,
            user_context=context,
            language=language,
        )
        
        # Add boarding pass info to response
        result['boarding_pass'] = boarding_pass_info
        
        # Persist updated context
        update_user_context(user_id, result.get("context", {}))
        
        return ChatResponse(**result)
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(image_path):
            os.unlink(image_path)
        
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")