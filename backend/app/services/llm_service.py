# backend/app/services/llm_service.py

import re

import httpx
from app.config import OLLAMA_URL, MODEL_NAME

FALLBACK_RESPONSE = "Sorry, I couldn't process that right now. Server error"


def polish_llm_markdown(text: str) -> str:
    """Normalize whitespace so Markdown renders cleanly in the chat UI."""
    t = (text or "").strip()
    if not t:
        return t
    t = re.sub(r"\r\n?", "\n", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{4,}", "\n\n\n", t)
    return t.strip()


async def call_llm(prompt: str) -> str:
    """
    Async call to local Ollama LLM.
    Expects a fully constructed prompt.
    Returns generated response or fallback.
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.4,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload
            )

        response.raise_for_status()
        data = response.json()

        raw = (data.get("response") or "").strip()
        return polish_llm_markdown(raw) if raw else FALLBACK_RESPONSE

    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return FALLBACK_RESPONSE