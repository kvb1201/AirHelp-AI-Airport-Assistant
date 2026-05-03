# backend/app/services/location_mapping_engine.py

from typing import Dict, Optional
from app.services.location_index import LOCATION_INDEX


def _match_label(text: str) -> Optional[str]:
    text = text.lower()

    for item in LOCATION_INDEX:
        for alias in item["aliases"]:
            if alias in text:
                return item["label"]

    return None


def map_locations(
    query: str,
    source_candidates: Optional[list] = None,
    semantic_candidates: Optional[Dict] = None,
) -> Dict:
    """
    Combine regex + semantic → final structured location
    """

    result = {
        "source": None,
        "destination": None,
        "confidence": "low",
    }

    # -----------------------
    # 1. Regex candidates (highest priority)
    # -----------------------
    if source_candidates:
        result["source"] = source_candidates[0]
        result["confidence"] = "high"
        return result

    # -----------------------
    # 2. Semantic fallback
    # -----------------------
    if semantic_candidates and semantic_candidates.get("label"):
        label = semantic_candidates["label"]

        mapped = _match_label(label)

        if mapped:
            result["source"] = mapped
            result["confidence"] = "medium"
            return result

    # -----------------------
    # 3. Direct query match fallback
    # -----------------------
    mapped = _match_label(query)
    if mapped:
        result["source"] = mapped
        result["confidence"] = "medium"

    return result