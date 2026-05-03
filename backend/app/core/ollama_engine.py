"""
AirportAI Engine - Ollama + NLLB-200 + Whisper Integration
Handles: Transliteration → Translation → LLM → Back-Translation
FULLY OFFLINE - No external API calls
"""

import os
import requests
from typing import Optional, Dict
from normalization import clean_input
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from app.utils.logger import logger
from app.core.slang_normalizer import clean_airport_slang

# ── OFFLINE MODE CONFIGURATION ──────────────────────────────────────────────────
# Set Hugging Face to use local cache only (no internet calls)
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Try to import ai4bharat, fall back to simple transliteration
try:
    from ai4bharat_transliteration import XlitEngine
    HAS_XLIT = True
except ImportError:
    HAS_XLIT = False
    logger.warning("ai4bharat not available, using simplified transliteration")


class SimpleTransliterator:
    """Fallback simple transliteration when ai4bharat is not available."""
    
    # Common Hinglish patterns → simple approximation
    HINGLISH_PATTERNS = {
        # Common Hinglish phrases - just detect and keep for NLLB-200
        # NLLB-200 can handle romanized input to some degree
    }
    
    def is_hinglish(self, text: str) -> bool:
        """Check if text is Hinglish (Roman script Hindi)."""
        # If it contains Latin characters and common Hindi words in Roman
        hinglish_words = ['hai', 'kya', 'kahan', 'kidhar', 'hain', 'aur', 'mujhe', 'aapko']
        return any(word in text.lower() for word in hinglish_words)
    
    def translit(self, text: str, lang: str = "hi") -> str:
        """
        Simple transliteration - for Hinglish, mostly pass-through
        since NLLB-200 can handle romanized Hindi reasonably well.
        """
        # For Hinglish, keep as-is (NLLB-200 handles it)
        # For pure Roman, also keep as-is
        # In production, would use ai4bharat transliteration library
        return text


class AirportAI:
    """
    Main orchestrator for the offline Ollama pipeline.
    Handles multiple language support and audio input.
    """

    def __init__(self, lang: str = "hi", ollama_host: str = "http://localhost:11434"):
        """
        Initialize the AirportAI engine.
        
        Args:
            lang: Language code ('hi' for Hindi, 'gu' for Gujarati, etc.)
            ollama_host: URL to Ollama server
        """
        self.lang = lang
        self.ollama_host = ollama_host
        
        # Map language to NLLB-200 codes
        self.lang_codes = {
            "en": "eng_Latn",
            "hi": "hin_Deva",
            "gu": "guj_Gujr",
            "mr": "mar_Deva",
            "ta": "tam_Taml",
            "te": "tel_Telu",
            "kn": "kan_Knda",
            "ml": "mal_Mlym",
            "bn": "ben_Beng",
            "pa": "pan_Guru",
            "ur": "urd_Arab",
            "or": "ory_Orya",
            "as": "asm_Beng",
        }
        
        self.nllb_code = self.lang_codes.get(lang, "hin_Deva")
        
        logger.info(f"🚀 Initializing AirportAI for {lang} (NLLB code: {self.nllb_code})")
        
        # Load Transliteration Engine
        try:
            if HAS_XLIT:
                self.xlit = XlitEngine(src_script_type="roman", beam_width=5)
                logger.info("✅ Transliteration engine (ai4bharat) loaded")
            else:
                self.xlit = SimpleTransliterator()
                logger.info("✅ Transliteration engine (simplified) loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load transliteration engine: {e}")
            self.xlit = SimpleTransliterator()

        # Load Speech-to-Text (Whisper) — lazy import so missing package doesn't crash startup
        try:
            from faster_whisper import WhisperModel
            self.stt = WhisperModel("base", device="cpu", compute_type="int8")
            logger.info("✅ Whisper STT model loaded")
        except ImportError:
            logger.warning("⚠️  faster_whisper not installed — STT disabled. Run: pip install faster-whisper")
            self.stt = None
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper: {e}")
            self.stt = None

        # Load NLLB-200 Translation Model
        try:
            model_name = "facebook/nllb-200-distilled-600M"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            logger.info("✅ NLLB-200 translation model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load NLLB-200: {e}")
            raise

    def _check_ollama(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file to text using Whisper.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        if self.stt is None:
            raise RuntimeError("Whisper STT model is not loaded. Install faster-whisper.")
        try:
            segments, _ = self.stt.transcribe(audio_path)
            text = "".join([segment.text for segment in segments])
            logger.info(f"📝 Transcribed: {text}")
            return text
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise

    def transliterate_text(self, text: str) -> str:
        """
        Convert Roman script (Hinglish) to native script.
        
        Args:
            text: Roman script text
            
        Returns:
            Native script text
        """
        try:
            cleaned = clean_input(text)
            
            # Handle both XlitEngine and SimpleTransliterator
            if isinstance(self.xlit, SimpleTransliterator):
                native_text = self.xlit.translit(cleaned, self.lang)
            else:
                result = self.xlit.translit_sentence(cleaned, self.lang)
                native_text = result.get(self.lang, cleaned)
            
            logger.info(f"🔤 Transliterated: {native_text}")
            return native_text
        except Exception as e:
            logger.error(f"❌ Transliteration failed: {e}")
            return text

    def _get_lang_id(self, lang_code: str) -> int:
        """Get language ID from tokenizer."""
        try:
            # Use convert_tokens_to_ids which is the standard way for NLLB
            token_id = self.tokenizer.convert_tokens_to_ids(lang_code)
            if token_id is not None and token_id != self.tokenizer.unk_token_id:
                return token_id
            
            # Default fallback for NLLB special tokens
            logger.warning(f"Could not resolve language ID for {lang_code}, falling back to 256047 (eng_Latn)")
            return 256047  # Default to English instead of 258 (Romanian)
        except Exception as e:
            logger.warning(f"Error resolving language ID for {lang_code}: {e}")
            return 256047

    def translate_to_english(self, text: str) -> str:
        """
        Translate from native language to English using NLLB-200.
        
        Args:
            text: Text in native language
            
        Returns:
            English translation
        """
        try:
            # NLLB requires src_lang set on the tokenizer before encoding
            self.tokenizer.src_lang = self.nllb_code
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            eng_token_id = self._get_lang_id("eng_Latn")
            tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=eng_token_id,
                max_new_tokens=256,
            )
            english_text = self.tokenizer.batch_decode(tokens, skip_special_tokens=True)[0]
            logger.info(f"🌐 Translated to English: {english_text}")
            return english_text
        except Exception as e:
            logger.error(f"❌ Translation to English failed: {e}")
            return text

    def translate_to_native(self, text: str) -> str:
        """
        Translate from English to native language using NLLB-200.
        
        Args:
            text: English text
            
        Returns:
            Native language translation
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for translation to native")
            return text
            
        try:
            # Source is always English when translating back to native
            self.tokenizer.src_lang = "eng_Latn"
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            lang_id = self._get_lang_id(self.nllb_code)
            logger.info(f"Translating to {self.lang} (code: {self.nllb_code}, ID: {lang_id})")
            
            tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=lang_id,
                max_new_tokens=256,
            )
            native_text = self.tokenizer.batch_decode(tokens, skip_special_tokens=True)[0]
            logger.info(f"🌐 Translated to {self.lang}: {native_text}")
            return native_text
        except Exception as e:
            logger.error(f"❌ Translation to native failed: {e}. Returning original text.")
            logger.error(f"   Language: {self.lang}, Code: {self.nllb_code}")
            # Return original text if translation fails
            return text

    def query_ollama(self, prompt: str, model: str = "gemma:2b") -> str:
        """
        Query Ollama (Gemma model) for response.
        
        Args:
            prompt: The prompt to send
            model: Model name (default: gemma:2b)
            
        Returns:
            Response from Gemma
        """
        if not self._check_ollama():
            error_msg = f"❌ Ollama not running at {self.ollama_host}. Start with: ollama run {model}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)

        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            gemma_response = result.get("response", "")
            logger.info(f"🤖 Gemma response: {gemma_response[:100]}...")
            return gemma_response
        except Exception as e:
            logger.error(f"❌ Ollama query failed: {e}")
            raise

    def pipe(
        self,
        user_input: str,
        is_audio: bool = False,
        airport_context: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Complete pipeline: Input → Translation → LLM → Back-Translation.
        
        Args:
            user_input: User input (text or path to audio)
            is_audio: Flag if input is an audio file path
            airport_context: Optional context string
            
        Returns:
            A dictionary containing the final response and intermediate steps.
        """
        
        processed_text = ""
        english_query = ""
        
        # 1. Handle Input: Transcribe if audio, otherwise use text
        if is_audio:
            processed_text = self.transcribe_audio(user_input)
        else:
            processed_text = user_input

        # 2. Apply slang normalization for all inputs (especially Hinglish/Hindi)
        slang_result = clean_airport_slang(processed_text)
        processed_text = slang_result
        
        # 3. Fast path: English-only processing (skip translation and LLM for simple cases)
        if self.lang == "en":
            logger.info("🚀 English-only mode - checking if LLM is needed")
            cleaned_text = clean_input(processed_text)
            
            # For simple queries that don't need LLM processing, return directly
            simple_patterns = ["hello", "hi", "hey", "gate", "terminal", "flight", "where is", "what time", "how to"]
            if any(pattern in cleaned_text.lower() for pattern in simple_patterns) and len(cleaned_text.split()) <= 5:
                logger.info("🚀 Simple English query detected - skipping LLM, returning direct response")
                return {
                    "original_input": user_input,
                    "processed_text": cleaned_text,
                    "english_query": cleaned_text,
                    "gemma_response": "",  # No LLM call needed
                    "final_response": cleaned_text,
                    "language": "en",
                }
            
            # For more complex English queries, still use LLM but skip translation
            final_prompt = f"You are an airport assistant. Answer the following question: {cleaned_text}"
            if airport_context:
                final_prompt += f"\n\nUse this context: {airport_context}"
            
            gemma_response = self.query_ollama(final_prompt)
            
            return {
                "original_input": user_input,
                "processed_text": cleaned_text,
                "english_query": cleaned_text,
                "gemma_response": gemma_response,
                "final_response": gemma_response,  # No translation needed for English
                "language": "en",
            }

        # 3. Normalize and Transliterate if not English
        if self.lang != "en":
            native_text = self.transliterate_text(processed_text)
            # 4. Translate to English
            english_query = self.translate_to_english(native_text)
        else:
            # If the language is English, just clean the input
            english_query = clean_input(processed_text)

        # 5. Construct Prompt for Ollama
        # Basic prompt, can be enhanced with a template from prompts.py
        final_prompt = f"You are an airport assistant. Answer the following question: {english_query}"
        if airport_context:
            final_prompt += f"\n\nUse this context: {airport_context}"

        # 6. Query the LLM
        gemma_response = self.query_ollama(final_prompt)

        # 7. Translate response back to native language if needed
        if self.lang != "en":
            final_response = self.translate_to_native(gemma_response)
        else:
            final_response = gemma_response
            
        return {
            "original_input": user_input,
            "processed_text": processed_text,
            "english_query": english_query,
            "gemma_response": gemma_response,
            "final_response": final_response,
            "language": self.lang,
        }
