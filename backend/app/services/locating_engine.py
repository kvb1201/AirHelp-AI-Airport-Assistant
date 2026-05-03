# backend/app/services/locating_engine.py

import re
from typing import Dict, Optional


# -------------------------------
# 🔹 Normalize Helpers
# -------------------------------
def _normalize_terminal(num: str) -> str:
    return f"terminal_{num}"


def _normalize_gate(letter: str, number: str) -> str:
    return f"gate_{letter.upper()}{number}"


# -------------------------------
# 🔹 Extract Terminal
# -------------------------------
def extract_terminal(text: str) -> Optional[str]:
    match = re.search(r"\bterminal\s*([1-3])\b", text.lower())
    if match:
        return _normalize_terminal(match.group(1))
    return None


# -------------------------------
# 🔹 Extract Gate
# -------------------------------
def extract_gate(text: str) -> Optional[str]:
    match = re.search(r"\bgate\s*([a-zA-Z])(\d+)\b", text.lower())
    if match:
        return _normalize_gate(match.group(1), match.group(2))
    return None


# -------------------------------
# 🔹 Detect Directional Intent
# -------------------------------
def extract_direction(text: str) -> Dict[str, Optional[str]]:
    text = text.lower()

    result = {
        "source": None,
        "destination": None,
    }

    # Example: "from terminal 1 to gate B12"
    from_match = re.search(r"from\s+(.*?)(to|$)", text)
    to_match = re.search(r"to\s+(.*)", text)

    if from_match:
        result["source"] = extract_location(from_match.group(1))

    if to_match:
        result["destination"] = extract_location(to_match.group(1))

    return result


# -------------------------------
# 🔹 Extract Location (fallback)
# -------------------------------
def extract_location(text: str) -> Optional[str]:
    # priority: gate > terminal
    gate = extract_gate(text)
    if gate:
        return gate

    terminal = extract_terminal(text)
    if terminal:
        return terminal

    return None


# -------------------------------
# 🔹 Detect "near" bias
# -------------------------------
def extract_near(text: str) -> Optional[str]:
    match = re.search(r"near\s+(.*)", text.lower())
    if match:
        return extract_location(match.group(1))
    return None


# -------------------------------
# 🔹 Main Locating Engine
# -------------------------------
def locate_from_query(message: str) -> Dict:
    """
    Extract structured location + navigation signals.

    Returns:
    {
        "location": inferred current location,
        "destination": inferred target,
        "explicit": bool (user explicitly mentioned location)
    }
    """

    message = message.lower()

    direction = extract_direction(message)
    near_location = extract_near(message)

    fallback_location = extract_location(message)

    location = None
    destination = None
    explicit = False

    # -------------------------------
    # 🔥 Priority Logic
    # -------------------------------

    # Case 1: "from X to Y"
    if direction["source"] or direction["destination"]:
        location = direction["source"]
        destination = direction["destination"]
        explicit = True

    # Case 2: "near X"
    elif near_location:
        location = near_location
        explicit = True

    # Case 3: only one location mentioned
    elif fallback_location:
        location = fallback_location
        explicit = True

    return {
        "location": location,
        "destination": destination,
        "explicit": explicit,
    }