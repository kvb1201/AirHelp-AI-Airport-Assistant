# backend/app/api/transcribe.py

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.core.stt_cache import stt_cache
from app.utils.logger import logger
import tempfile
import os

router = APIRouter()

class TranscribeResponse(BaseModel):
    transcript: str
    detected_language: str
    language_probability: float

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_endpoint(
    file: UploadFile = File(...),
    language: str = None
):
    """
    Transcribe audio file using Whisper STT.
    
    Args:
        file: Audio file to transcribe
        language: Optional target language code (e.g., 'hi', 'en')
    
    Returns:
        Transcription result with detected language info
    """
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type, audio expected.")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await file.read()
        tmp.write(content)
        audio_path = tmp.name
    
    try:
        # Transcribe using cached Whisper
        if language:
            transcript, detected_lang, lang_prob = await stt_cache.transcribe_with_language(
                audio_path, target_language=language
            )
        else:
            transcript, detected_lang, lang_prob = await stt_cache.transcribe(audio_path)
        
        # Clean up temp file
        os.unlink(audio_path)
        
        return TranscribeResponse(
            transcript=transcript,
            detected_language=detected_lang,
            language_probability=lang_prob
        )
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(audio_path):
            os.unlink(audio_path)
        
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
