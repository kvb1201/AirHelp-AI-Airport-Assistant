# backend/app/services/locating_engine.py

from typing import Dict, Optional

from app.services.location_semantic_engine import semantic_resolve
from app.services.location_mapping_engine import map_locations


# -------------------------------
# 🔹 Intent Keywords
# -------------------------------
INTENT_KEYWORDS = {
    "food": ["food", "eat", "restaurant"],
    "coffee": ["coffee", "cafe"],
    "lounge": ["lounge"],
    "atm": ["atm", "cash"],
    "wifi": ["wifi", "internet"],
    "shop": ["shop", "buy"],
    "explore": ["what can i do", "things to do", "explore", "around", "nearby"],
}


# -------------------------------
# 🔹 Service Labels (NOT locations)
# -------------------------------
SERVICE_LABELS = frozenset(
    {
        "lounge",
        "wifi",
        "atm",
        "food",
        "coffee",
        "shop",
        "restaurant",
        "retail",
        "dining",
    }
)


# -------------------------------
# 🔹 Detect Query Type
# -------------------------------
def _detect_query_type(text: str) -> str:
    t = text.lower()

    # Destination-type queries (must include "take me to" etc. or mapped gates land as *source* by mistake)
    if any(
        x in t
        for x in [
            "go to",
            "want to go to",
            "going to",
            "need to go to",
            "need to get to",
            "navigate to",
            "take me to",
            "walk me to",
            "guide me to",
            "directions to",
            "route to",
            "path to",
            "way to",
            "how do i get to",
            "how do i go to",
            "how to get to",
            "how to go to",
            "redirect to",
            "redirect me to",
            "where is",
            "where's",
            "wheres",
            "get to",
            "get me to",
            "point me to",
            "help me get",
            "help me find",
            "which way",
            "nearest",
        ]
    ):
        return "destination"

    # Source-type queries
    if any(x in t for x in ["i am", "i'm at", "im at", "near", "at gate", "currently at"]):
        return "source"

    return "intent"


# -------------------------------
# 🔹 Extract Intent
# -------------------------------
def _extract_intent(text: str) -> Optional[str]:
    t = text.lower()

    # 🔥 Strong explicit check for explore
    if any(x in t for x in ["something to do", "what can i do", "things to do", "explore"]):
        return "explore"

    for intent, keywords in INTENT_KEYWORDS.items():
        if any(k in t for k in keywords):
            return intent

    return None


# -------------------------------
# 🔹 MAIN LOCATING ENGINE
# -------------------------------
def locate_from_query(message: str) -> Dict:
    """
    Extract structured information:
    - source (user location)
    - destination (target place/service)
    - intent
    """

    # -------------------------------
    # STEP 1: Query Type
    # -------------------------------
    query_type = _detect_query_type(message)

    # -------------------------------
    # STEP 2: Intent
    # -------------------------------
    intent = _extract_intent(message)

    # -------------------------------
    # STEP 3: Semantic Layer
    # -------------------------------
    semantic_output = semantic_resolve(message)

    # -------------------------------
    # STEP 4: Mapping Layer
    # -------------------------------
    mapping_output = map_locations(
        query=message,
        source_candidates=None,
        semantic_candidates=semantic_output,
    )

    # -------------------------------
    # STEP 5: Decision Layer
    # -------------------------------
    source = None
    destination = None

    mapped_location = mapping_output.get("source")

    if mapped_location:

        # 🔥 FIX 1 — Service vs Location
        if mapped_location in SERVICE_LABELS:
            destination = mapped_location

        # 🔥 Destination-style queries
        elif query_type == "destination":
            destination = mapped_location

        # 🔥 Otherwise treat as source
        else:
            source = mapped_location

    # -------------------------------
    # STEP 6: Confidence
    # -------------------------------
    confidence_map = {
        "high": 0.9,
        "medium": 0.7,
        "low": 0.4,
    }

    confidence = confidence_map.get(mapping_output.get("confidence"), 0.5)

    # -------------------------------
    # STEP 7: Missing Both
    # -------------------------------
    if source is None and destination is None:
        return {
            "source": None,
            "destination": None,
            "intent": intent,
            "needs_clarification": True,
            "clarification_message": "Where are you currently? For example: Terminal 1, Gate A1.",
            "confidence": 0.0,
        }

    # -------------------------------
    # STEP 8: Destination but no source
    # (Handled by context engine later)
    # -------------------------------
    if destination and source is None:
        return {
            "source": None,
            "destination": destination,
            "intent": intent,
            "needs_clarification": False,
            "clarification_message": None,
            "confidence": confidence,
            "meta": "source_missing",
        }

    # -------------------------------
    # STEP 9: Final Output
    # -------------------------------
    return {
        "source": source,
        "destination": destination,
        "intent": intent,
        "needs_clarification": False,
        "clarification_message": None,
        "confidence": confidence,
    }