# backend/app/services/context_engine.py

from typing import Dict, Any
from datetime import datetime


# -------------------------------
# 🔹 Safe Getter
# -------------------------------
def _safe_get(d: Dict, key: str, default=None):
    return d[key] if key in d else default


# -------------------------------
# 🔹 Update Context (CORE ENGINE)
# -------------------------------
def update_context(
    user_context: Dict[str, Any],
    extracted: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Updates and enriches user context using extracted signals.

    Responsibilities:
    - Maintain location + destination
    - Preserve session memory
    - Add recency (last_query, timestamp)
    - Handle ambiguity safely
    """

    updated = dict(user_context)

    new_location = extracted.get("location")
    new_destination = extracted.get("destination")
    explicit = extracted.get("explicit", False)

    # -------------------------------
    # 🔥 1. LOCATION HANDLING
    # -------------------------------
    if new_location:
        updated["location"] = new_location

    elif not updated.get("location"):
        # fallback default (important)
        updated["location"] = "entrance"

    # -------------------------------
    # 🔥 2. DESTINATION HANDLING
    # -------------------------------
    if new_destination:
        updated["destination"] = new_destination

    # -------------------------------
    # 🔥 3. CONTEXT MEMORY (VERY IMPORTANT)
    # -------------------------------
    updated["last_query"] = extracted.get("raw_query", None)
    updated["last_updated"] = datetime.utcnow().isoformat()

    # -------------------------------
    # 🔥 4. INTENT BIAS FLAGS
    # -------------------------------
    # Helps orchestrator behave smarter later
    updated["has_explicit_location"] = explicit

    # Example: if user already navigating → maintain state
    if _safe_get(updated, "last_route"):
        updated["in_navigation"] = True
    else:
        updated["in_navigation"] = False

    # -------------------------------
    # 🔥 5. STABILITY FIXES
    # -------------------------------
    # Prevent wiping important fields accidentally
    updated.setdefault("destination", None)
    updated.setdefault("last_route", None)
    updated.setdefault("last_recommendations", None)

    return updated