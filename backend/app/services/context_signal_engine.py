# backend/app/services/context_signal_engine.py

from typing import Dict, Optional
from app.services.shared_embedder import get_embedder


# -----------------------------------------------
# 🔹 Semantic Labels (for intent classification)
# -----------------------------------------------
INTENT_LABELS = [
    "food",
    "restaurant",
    "coffee",
    "lounge",
    "atm",
    "wifi",
    "shop",
    "explore",
    "things to do",
]


# -----------------------------------------------
# 🔹 Lazy Init Embeddings
# -----------------------------------------------
_label_embeddings = None


def _init_embeddings():
    global _label_embeddings

    if _label_embeddings is None:
        embedder = get_embedder()
        _label_embeddings = embedder.encode(INTENT_LABELS)


# -----------------------------------------------
# 🔹 Semantic Intent Detection
# -----------------------------------------------
def _semantic_intent(message: str) -> Dict:
    _init_embeddings()

    embedder = get_embedder()
    query_vec = embedder.encode([message])[0]

    # cosine similarity
    scores = (query_vec @ _label_embeddings.T)

    best_idx = scores.argmax()
    best_score = float(scores[best_idx])

    return {
        "label": INTENT_LABELS[best_idx],
        "score": best_score,
    }


# -----------------------------------------------
# 🔹 MAIN SIGNAL EXTRACTION
# -----------------------------------------------
def extract_signals(message: str) -> Dict:
    """
    Extracts:
    - intent
    - behavior

    Rules:
    - behavior must NOT leak across queries
    - semantic must have strong confidence
    """

    text = message.lower()

    # -------------------------------
    # 🔹 Intent (rule-first)
    # -------------------------------
    intent: Optional[str] = None

    if any(x in text for x in ["food", "eat", "restaurant"]):
        intent = "food"

    elif any(x in text for x in ["coffee", "cafe"]):
        intent = "coffee"

    elif "lounge" in text:
        intent = "lounge"

    elif "atm" in text:
        intent = "atm"

    elif "wifi" in text:
        intent = "wifi"

    elif any(x in text for x in ["shop", "buy"]):
        intent = "shop"

    elif any(x in text for x in ["explore", "things to do"]):
        intent = "explore"

    # -------------------------------
    # 🔹 Semantic Intent (fallback)
    # -------------------------------
    semantic_output = _semantic_intent(message)
    semantic_label = semantic_output["label"]
    semantic_score = semantic_output["score"]

    if intent is None and semantic_score >= 0.6:
        if semantic_label in ["food", "restaurant"]:
            intent = "food"
        elif semantic_label == "coffee":
            intent = "coffee"
        elif semantic_label == "lounge":
            intent = "lounge"
        elif semantic_label == "atm":
            intent = "atm"
        elif semantic_label == "wifi":
            intent = "wifi"
        elif semantic_label == "shop":
            intent = "shop"
        elif semantic_label in ["explore", "things to do"]:
            intent = "explore"

    # -------------------------------
    # 🔹 Behavior (FIXED — no leakage)
    # -------------------------------
    behavior: Optional[str] = None

    # ⚡ Rule-based detection
    if any(x in text for x in ["quick", "fast", "hurry", "rush"]):
        behavior = "quick"

    elif any(x in text for x in ["relax", "rest", "comfortable", "calm"]):
        behavior = "relaxed"

    # 🧠 Semantic fallback (only strong signals)
    elif semantic_score >= 0.6:
        if semantic_label in ["fast food", "grab", "quick bite"]:
            behavior = "quick"

        elif semantic_label in ["lounge", "rest", "relax"]:
            behavior = "relaxed"

    # -------------------------------
    # 🔹 Final Output
    # -------------------------------
    return {
        "intent": intent,
        "behavior": behavior,
        "semantic_score": semantic_score,
    }