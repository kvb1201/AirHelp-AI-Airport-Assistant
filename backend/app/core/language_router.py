# backend/app/core/language_router.py

"""
Language Router — Smart pipeline routing based on input language + mode.

Rules:
  1. English (voice or text)   → Skip translation. Send directly to orchestrator.
  2. Hinglish (typed text)     → Slang map → send cleaned English to Gemma/orchestrator.
  3. Other language (voice/text) → Translate to English → forward to orchestrator.
"""

import re
from typing import Dict, Optional, Tuple
from app.utils.logger import logger
from app.core.slang_normalizer import slang_normalizer


# ── Language Detection ──────────────────────────────────────────────────────

# Unicode block checks
_DEVANAGARI_RE  = re.compile(r'[\u0900-\u097F]')  # Hindi, Marathi, Sanskrit
_GUJARATI_RE    = re.compile(r'[\u0A80-\u0AFF]')
_TAMIL_RE       = re.compile(r'[\u0B80-\u0BFF]')
_TELUGU_RE      = re.compile(r'[\u0C00-\u0C7F]')
_KANNADA_RE     = re.compile(r'[\u0C80-\u0CFF]')
_MALAYALAM_RE   = re.compile(r'[\u0D00-\u0D7F]')
_BENGALI_RE     = re.compile(r'[\u0980-\u09FF]')
_GURMUKHI_RE    = re.compile(r'[\u0A00-\u0A7F]')  # Punjabi
_ARABIC_RE      = re.compile(r'[\u0600-\u06FF\uFE70-\uFEFF]')  # Urdu / Arabic
_ODIA_RE        = re.compile(r'[\u0B00-\u0B7F]')

_NATIVE_SCRIPT_CHECKS = {
    "hi": _DEVANAGARI_RE,
    "mr": _DEVANAGARI_RE,
    "gu": _GUJARATI_RE,
    "ta": _TAMIL_RE,
    "te": _TELUGU_RE,
    "kn": _KANNADA_RE,
    "ml": _MALAYALAM_RE,
    "bn": _BENGALI_RE,
    "pa": _GURMUKHI_RE,
    "ur": _ARABIC_RE,
    "or": _ODIA_RE,
}

# NLLB-200 language codes
LANG_TO_NLLB = {
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


def _has_native_script(text: str) -> Optional[str]:
    """Return the language code if text contains any native (non-Latin) script, else None."""
    for lang, pattern in _NATIVE_SCRIPT_CHECKS.items():
        if pattern.search(text):
            return lang
    return None


def _is_pure_english(text: str) -> bool:
    """
    Return True if text is standard English — only ASCII / basic Latin chars,
    no Hinglish indicators.
    """
    # Strip punctuation & digits for the check
    alpha_only = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    if not alpha_only:
        return False

    # Must be ASCII letters
    try:
        alpha_only.encode('ascii')
    except UnicodeEncodeError:
        return False

    # Check against Hinglish indicators
    return not slang_normalizer.is_hinglish_input(text)


def _is_hinglish(text: str) -> bool:
    """
    Detect Hinglish: Latin-script text containing Hindi/Indic word patterns.
    """
    # Must be Latin script (ASCII-encodable)
    stripped = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    if not stripped:
        return False
    try:
        stripped.encode('ascii')
    except UnicodeEncodeError:
        return False

    # Use the existing slang normalizer's detection
    return slang_normalizer.is_hinglish_input(text)


def detect_language(text: str, input_mode: str = "text", whisper_lang: str = None) -> str:
    """
    Detect the language category of the input.

    Args:
        text: The user's input text
        input_mode: "text" or "voice"
        whisper_lang: Language code from Whisper STT (if voice input)

    Returns:
        One of: "english", "hinglish", "native_<lang_code>"
    """
    # If voice input and Whisper detected a language
    if input_mode == "voice" and whisper_lang:
        if whisper_lang == "en":
            return "english"
        # Whisper detected a non-English language (will use passthrough since NLLB is disabled)
        return f"native_{whisper_lang}"

    # Check for native scripts (Devanagari, Tamil, etc.)
    native_lang = _has_native_script(text)
    if native_lang:
        return f"native_{native_lang}"

    # Check if it's Hinglish (Latin script with Hindi words) — only for typed text
    if input_mode == "text" and _is_hinglish(text):
        return "hinglish"

    # Default: treat as English
    return "english"


# ── Pipeline Router ─────────────────────────────────────────────────────────

def route_input(
    text: str,
    input_mode: str = "text",
    whisper_lang: str = None,
) -> Dict[str, str]:
    """
    Route user input through the correct pipeline.

    Args:
        text: Raw user input (transcribed text if voice)
        input_mode: "text" or "voice"
        whisper_lang: Language detected by Whisper (for voice inputs)

    Returns:
        Dict with:
          - "english_text": The cleaned English text to send to orchestrator
          - "detected_lang": The detected language category
          - "original_text": The original input
          - "pipeline": Which pipeline was used ("direct", "slang_map", "translation")
    """
    detected = detect_language(text, input_mode, whisper_lang)

    logger.info(f"🌐 Language Router: input_mode={input_mode}, detected={detected}")

    # ── RULE 1: English → skip everything, send directly ──
    if detected == "english":
        logger.info("🟢 Pipeline: DIRECT (English) — no translation needed")
        return {
            "english_text": text,
            "detected_lang": "english",
            "original_text": text,
            "pipeline": "direct",
        }

    # ── RULE 2: Hinglish (typed) → slang map → clean English ──
    if detected == "hinglish":
        logger.info("🟡 Pipeline: SLANG MAP (Hinglish) → Gemma")
        result = slang_normalizer.process_input(text, is_hinglish=True)
        cleaned = result["cleaned"]
        logger.info(f"   Slang map: '{text}' → '{cleaned}'")
        return {
            "english_text": cleaned,
            "detected_lang": "hinglish",
            "original_text": text,
            "pipeline": "slang_map",
        }

    # ── RULE 3: Other language (voice or typed) → translate to English ──
    if detected.startswith("native_"):
        lang_code = detected.replace("native_", "")
        logger.info(f"🔴 Pipeline: TRANSLATION ({lang_code} → English)")

        nllb_src = LANG_TO_NLLB.get(lang_code, "hin_Deva")
        nllb_tgt = "eng_Latn"

        # Try to use the translation engine
        try:
            from app.core.translation_engine import translation_engine
            result = translation_engine.translate(text, nllb_src, nllb_tgt)
            english_text = result.get("translation", text)
            logger.info(f"   Translated: '{text[:60]}...' → '{english_text[:60]}...'")
        except Exception as e:
            logger.error(f"   Translation failed: {e}, passing text through")
            english_text = text

        return {
            "english_text": english_text,
            "detected_lang": detected,
            "original_text": text,
            "pipeline": "translation",
        }

    # Fallback: treat as English
    logger.info("🟢 Pipeline: DIRECT (fallback)")
    return {
        "english_text": text,
        "detected_lang": "english",
        "original_text": text,
        "pipeline": "direct",
    }
