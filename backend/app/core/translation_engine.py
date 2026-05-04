# backend/app/core/translation_engine.py

"""
Translation Engine using NLLB-200
Handles direct text translation between languages
"""

import os
from typing import Dict, Optional
from app.utils.logger import logger

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    logger.warning("transformers not installed. Translation will use mock responses.")
    HAS_TRANSFORMERS = False

# Force offline mode
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

class TranslationEngine:
    """Translation engine using NLLB-200 model"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.translator = None
        self._load_model()
    
    def _load_model(self):
        """Load NLLB-200 translation model"""
        if not HAS_TRANSFORMERS:
            return
            
        try:
            model_name = "facebook/nllb-200-distilled-600M"
            logger.info(f"Loading translation model: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            # Create translation pipeline
            self.translator = pipeline(
                "translation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1  # CPU
            )
            
            logger.info("✅ Translation model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load translation model: {e}")
            self.model = None
            self.tokenizer = None
            self.translator = None
    
    def translate(self, text: str, src_lang: str, tgt_lang: str) -> Dict[str, any]:
        """
        Translate text from source to target language
        """
        if not self.translator:
            # Fallback: return mock translation
            logger.warning("Translation model not available, returning mock translation")
            mock_translation = f"[Mock Translation to {tgt_lang}]: {text}"
            return {
                "translation": mock_translation,
                "confidence": 0.0
            }
        
        try:
            # Perform translation
            result = self.translator(
                text,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                max_length=512
            )
            
            if isinstance(result, list) and len(result) > 0:
                translation = result[0]['translation_text']
            elif isinstance(result, dict):
                translation = result.get('translation_text', text)
            else:
                translation = str(result)
            
            logger.info(f"Translation successful: {translation[:100]}...")
            
            return {
                "translation": translation,
                "confidence": 0.9
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {
                "translation": text,
                "confidence": 0.0,
                "error": str(e)
            }

# Global instance
translation_engine = TranslationEngine()
