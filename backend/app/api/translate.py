# backend/app/api/translate.py

"""
Translation API Endpoint
Provides direct translation using NLLB-200 model
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.translation_engine import translation_engine
from app.utils.logger import logger

router = APIRouter()

class TranslationRequest(BaseModel):
    text: str
    src_lang: str = "eng_Latn"
    tgt_lang: str = "hin_Deva"

class TranslationResponse(BaseModel):
    translation: str
    src_lang: str
    tgt_lang: str
    confidence: Optional[float] = None

@router.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text from source language to target language using NLLB-200.
    
    Args:
        request: Translation request with text and language codes
        
    Returns:
        Translated text with metadata
    """
    try:
        logger.info(f"Translation request: {request.src_lang} -> {request.tgt_lang}")
        logger.info(f"Source text: {request.text[:100]}...")
        
        # Use the translation engine
        result = translation_engine.translate(
            request.text,
            request.src_lang,
            request.tgt_lang
        )
        
        return TranslationResponse(
            translation=result.get("translation", request.text),
            src_lang=request.src_lang,
            tgt_lang=request.tgt_lang,
            confidence=result.get("confidence", 0.5)
        )
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
