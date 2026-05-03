# backend/app/services/location_semantic_engine.py

from typing import Dict, Optional
from sentence_transformers import SentenceTransformer, util

# 🔹 Load ONCE (fast)
_model = None
_label_embeddings = None

# 🔹 Canonical labels (small + controlled)
LOCATION_LABELS = [
    "terminal 1",
    "terminal 2",
    "terminal 3",
    "gate a1",
    "gate b12",
    "gate d3",
    "lounge",
    "food court",
    "restaurant",
    "coffee shop",
    "atm",
    "restroom",
    "wifi",
    "check in",
]


def _get_model():
    global _model
    if _model is None:
        print("[Semantic] Loading MiniLM model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _init_label_embeddings():
    global _label_embeddings

    if _label_embeddings is None:
        model = _get_model()
        _label_embeddings = model.encode(LOCATION_LABELS, convert_to_tensor=True)


def semantic_resolve(text: str) -> Dict[str, Optional[str]]:
    """
    Semantic fallback for location detection
    """

    _init_label_embeddings()

    model = _get_model()
    query_emb = model.encode(text, convert_to_tensor=True)

    scores = util.cos_sim(query_emb, _label_embeddings)[0]

    best_idx = int(scores.argmax())
    best_score = float(scores[best_idx])
    best_label = LOCATION_LABELS[best_idx]

    print(f"[Semantic] Best match: {best_label} | score={best_score:.3f}")

    # 🔥 Threshold tuning (important)
    if best_score < 0.45:
        return {
            "label": None,
            "confidence": "low",
        }

    return {
        "label": best_label,
        "confidence": "medium",
    }