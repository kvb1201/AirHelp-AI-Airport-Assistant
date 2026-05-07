"""
Context Persistence Layer

PURPOSE:
    Control what gets persisted to users.json vs ephemeral session store.

CRITICAL RULE:
    ONLY these fields should be persisted to users.json:
    - user_id
    - flight_number, boarding_time, departure_time, terminal, gate
    - location, source (last stated location - session context)
    - alerts_sent
    - _operational_brief
    - created_at, updated_at

    NEVER persist:
    - intent (orchestration state)
    - mode (orchestration state)
    - selected (recommendation cache)
    - last_results (recommendation cache)
    - destination (navigation state)
    - behavior (can be session or preference)

CONTAMINATION FIX:
    Before: All fields persisted → stale state contamination
    After: Only profile + location persisted → clean state
"""

from typing import Dict, Any
from datetime import datetime, timezone, timedelta

# ============================================
# PERSISTENT FIELDS (users.json)
# ============================================

PERSISTENT_FIELDS = {
    # Identity
    "user_id",
    "created_at",
    "updated_at",
    
    # Flight information
    "flight_number",
    "boarding_time",
    "departure_time",
    "terminal",
    "gate",
    
    # Location context (session-level, but persisted for convenience)
    "location",
    "source",
    
    # Alert deduplication
    "alerts_sent",
    
    # Operational notices
    "_operational_brief",
}

# ============================================
# EPHEMERAL FIELDS (session store)
# ============================================

EPHEMERAL_FIELDS = {
    # Orchestration state (NEVER persist)
    "intent",
    "mode",
    "destination",
    
    # Recommendation cache (NEVER persist)
    "selected",
    "last_results",
    
    # Session preferences (could be persistent, but safer as ephemeral)
    "behavior",
}


def filter_persistent_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter context to only include fields that should be persisted.
    
    This is the CRITICAL function that prevents contamination.
    
    Args:
        context: Full context dict (may include ephemeral fields)
    
    Returns:
        Filtered context with only persistent fields
    
    Example:
        Input:  {"user_id": "123", "intent": "food", "mode": "navigation"}
        Output: {"user_id": "123"}
        
        "intent" and "mode" are REMOVED because they're ephemeral.
    """
    filtered = {}
    
    for key, value in context.items():
        if key in PERSISTENT_FIELDS:
            filtered[key] = value
        elif key in EPHEMERAL_FIELDS:
            # Explicitly skip ephemeral fields
            print(f"[PERSISTENCE] Skipping ephemeral field: {key}")
        else:
            # Unknown field - log warning but include it
            print(f"[PERSISTENCE] Warning: Unknown field '{key}', including in persistent storage")
            filtered[key] = value
    
    return filtered


def ensure_timestamps(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure created_at and updated_at timestamps exist.
    
    Args:
        context: Context dict
    
    Returns:
        Context with timestamps
    """
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist).isoformat()
    
    if "created_at" not in context:
        context["created_at"] = now
    
    context["updated_at"] = now
    
    return context


def prepare_for_persistence(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare context for persistence to users.json.
    
    This is the main function to call before saving to users.json.
    
    Steps:
        1. Filter to only persistent fields
        2. Ensure timestamps
        3. Validate required fields
    
    Args:
        context: Full context dict
    
    Returns:
        Clean context ready for persistence
    """
    # Filter ephemeral fields
    clean_context = filter_persistent_context(context)
    
    # Ensure timestamps
    clean_context = ensure_timestamps(clean_context)
    
    # Validate user_id exists
    if "user_id" not in clean_context:
        raise ValueError("user_id is required for persistence")
    
    return clean_context


def extract_ephemeral_state(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract ephemeral state from context.
    
    This is used to populate session store from context.
    
    Args:
        context: Full context dict
    
    Returns:
        Dict with only ephemeral fields
    """
    ephemeral = {}
    
    for key in EPHEMERAL_FIELDS:
        if key in context:
            ephemeral[key] = context[key]
    
    return ephemeral


def merge_persistent_and_ephemeral(
    persistent: Dict[str, Any],
    ephemeral: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge persistent context with ephemeral session state.
    
    Used when loading full context for orchestrator.
    
    Args:
        persistent: Context from users.json
        ephemeral: Session state from session store
    
    Returns:
        Merged context
    """
    merged = persistent.copy()
    merged.update(ephemeral)
    return merged


# ============================================
# MIGRATION HELPERS
# ============================================

def clean_legacy_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean legacy context that has ephemeral fields persisted.
    
    This is for migrating existing users.json data.
    
    Args:
        context: Legacy context with ephemeral fields
    
    Returns:
        Cleaned context
    """
    cleaned = filter_persistent_context(context)
    
    # Log what was removed
    removed = set(context.keys()) - set(cleaned.keys())
    if removed:
        print(f"[MIGRATION] Removed ephemeral fields from persistent storage: {removed}")
    
    return cleaned


def validate_no_ephemeral_in_persistent(context: Dict[str, Any]) -> bool:
    """
    Validate that context has no ephemeral fields.
    
    Use this as a sanity check before saving to users.json.
    
    Args:
        context: Context to validate
    
    Returns:
        True if clean, False if has ephemeral fields
    """
    has_ephemeral = any(key in EPHEMERAL_FIELDS for key in context.keys())
    
    if has_ephemeral:
        ephemeral_found = [key for key in context.keys() if key in EPHEMERAL_FIELDS]
        print(f"[VALIDATION] ERROR: Ephemeral fields found in persistent context: {ephemeral_found}")
        return False
    
    return True
