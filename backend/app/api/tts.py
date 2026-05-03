import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.tts_service import synthesize_wav, tts_status

router = APIRouter()
_log = logging.getLogger(__name__)


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2800)
    language: str = "en"  # ignored; English-only Piper


@router.get("/tts/status")
async def tts_status_endpoint() -> Dict[str, Any]:
    """Report Piper binary + which voice models are configured (for UI)."""
    return tts_status()


@router.post("/tts")
async def tts_speak(request: TtsRequest):
    """
    Synthesize speech offline via Piper. Returns audio/wav.
    """
    try:
        wav = await asyncio.to_thread(synthesize_wav, request.text, request.language)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        _log.warning("TTS /piper failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e

    return Response(content=wav, media_type="audio/wav")
