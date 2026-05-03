# backend/app/services/llm_service.py

import httpx
from app.config import OLLAMA_URL, MODEL_NAME

FALLBACK_RESPONSE = "Sorry, I couldn't process that right now. Server error"


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

        return data.get("response", "").strip() or FALLBACK_RESPONSE

    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return FALLBACK_RESPONSE