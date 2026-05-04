# backend/app/core/stt_cache.py

import os
import tempfile
from typing import Optional, Tuple
from app.utils.logger import logger

try:
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except ImportError:
    logger.warning("faster-whisper not installed. STT will use mock responses.")
    HAS_WHISPER = False

class STTCache:
    """Cached Whisper model for fast speech-to-text processing."""
    
    def __init__(self):
        self._model = None
        self._model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
        self._device = os.getenv("WHISPER_DEVICE", "cpu")
        
    def _load_model(self):
        """Lazy load the Whisper model."""
        if not HAS_WHISPER:
            return None
            
        if self._model is None:
            try:
                logger.info(f"Loading Whisper model: {self._model_size} on {self._device}")
                self._model = WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type="int8" if self._device == "cpu" else "float16"
                )
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                self._model = None
        return self._model
    
    async def transcribe(self, audio_path: str) -> Tuple[str, str, float]:
        """
        Transcribe audio file. Falls back to mock if model unavailable.
        """
        model = self._load_model()
        
        if model is None:
            logger.info("STT Mock: Returning placeholder transcription")
            return "This is a mock transcription because Whisper is not loaded.", "en", 1.0
            
        try:
            # Transcribe the audio
            segments, info = model.transcribe(
                audio_path,
                language=None,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=200)
            )
            
            transcript = " ".join(segment.text for segment in segments).strip()
            return transcript, info.language, info.language_probability
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return "Transcription failed.", "en", 0.0
    
    async def transcribe_with_language(self, audio_path: str, target_language: Optional[str] = None) -> Tuple[str, str, float]:
        """
        Transcribe with optional target language hint.
        """
        model = self._load_model()
        
        if model is None:
            return "Mock transcription (language hint ignored).", target_language or "en", 1.0
            
        try:
            segments, info = model.transcribe(
                audio_path,
                language=target_language,
                beam_size=5,
                vad_filter=True
            )
            
            transcript = " ".join(segment.text for segment in segments).strip()
            detected_language = info.language if info.language else target_language or "en"
            return transcript, detected_language, info.language_probability or 1.0
            
        except Exception as e:
            logger.error(f"Whisper transcription with language hint failed: {e}")
            return await self.transcribe(audio_path)

# Global instance
stt_cache = STTCache()
