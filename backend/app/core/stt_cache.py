
# backend/app/core/stt_cache.py

import os
import tempfile
from typing import Optional, Tuple
from faster_whisper import WhisperModel
from app.utils.logger import logger

class STTCache:
    """Cached Whisper model for fast speech-to-text processing."""
    
    def __init__(self):
        self._model: Optional[WhisperModel] = None
        self._model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
        self._device = os.getenv("WHISPER_DEVICE", "cpu")
        
    def _load_model(self) -> WhisperModel:
        """Lazy load the Whisper model."""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self._model_size} on {self._device}")
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type="int8" if self._device == "cpu" else "float16"
            )
            logger.info("Whisper model loaded successfully")
        return self._model
    
    async def transcribe(self, audio_path: str) -> Tuple[str, str, float]:
        """
        Transcribe audio file using cached Whisper model.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (transcript, detected_language, language_probability)
        """
        try:
            model = self._load_model()
            
            # Transcribe the audio
            segments, info = model.transcribe(
                audio_path,
                language=None,  # Auto-detect language
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=200)
            )
            
            # Get the full transcript
            transcript = " ".join(segment.text for segment in segments)
            
            # Clean up transcript
            transcript = transcript.strip()
            
            # Get detected language info
            detected_language = info.language
            language_probability = info.language_probability
            
            logger.info(f"Transcribed {len(transcript)} chars, detected: {detected_language} ({language_probability:.2f})")
            
            return transcript, detected_language, language_probability
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise e
    
    async def transcribe_with_language(self, audio_path: str, target_language: Optional[str] = None) -> Tuple[str, str, float]:
        """
        Transcribe with optional target language hint.
        
        Args:
            audio_path: Path to audio file
            target_language: Optional language code (e.g., 'hi', 'en')
            
        Returns:
            Tuple of (transcript, detected_language, language_probability)
        """
        try:
            model = self._load_model()
            
            # Transcribe with language hint if provided
            segments, info = model.transcribe(
                audio_path,
                language=target_language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=200)
            )
            
            transcript = " ".join(segment.text for segment in segments)
            transcript = transcript.strip()
            
            detected_language = info.language if info.language else target_language or "en"
            language_probability = info.language_probability if info.language_probability else 1.0
            
            return transcript, detected_language, language_probability
            
        except Exception as e:
            logger.error(f"Whisper transcription with language hint failed: {e}")
            # Fallback to auto-detection
            return await self.transcribe(audio_path)

# Global instance
stt_cache = STTCache()
