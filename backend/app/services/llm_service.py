import requests
from app.config import OLLAMA_URL, MODEL_NAME

FALLBACK_RESPONSE = "Sorry, I couldn't process that right now."


def call_llm(user_input: str) -> str:
    """
    Call the local Ollama instance with the Gemma model.
    Returns the generated text, or a safe fallback on failure.
    """
    prompt = (
        "You are an intelligent airport assistant. "
        "Help travelers with gates, food, shops, services, and navigation.\n\n"
        f"User: {user_input}\n\n"
        "Provide a helpful and concise response."
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.4,
        },
    }

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["response"]
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return FALLBACK_RESPONSE
