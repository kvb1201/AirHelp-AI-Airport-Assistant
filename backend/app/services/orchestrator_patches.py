"""
Orchestrator Patches for Contamination Fix

PURPOSE:
    Provide helper functions to refactor orchestrator.py without
    rewriting the entire file.

CRITICAL FIXES:
    1. Remove context["mode"] = "navigation" writes
    2. Remove context["intent"] persistence
    3. Remove context["selected"] persistence
    4. Remove context["last_results"] persistence
    5. Use session store instead

USAGE:
    Replace contaminating code with these clean helpers.
"""

from typing import Dict, Any, List, Optional
from app.core.session import (
    get_session,
    set_session,
    clear_session,
    invalidate_session_if_new_intent,
    get_navigation,
    set_navigation,
    complete_navigation,
    is_followup_query as session_is_followup_query,
)


# ============================================
# FOLLOW-UP HANDLING (Clean)
# ============================================

def handle_followup_query(
    user_input: str,
    user_id: str,
    user_context: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Handle follow-up queries using session store.
    
    CRITICAL: Only use session cache if:
        1. Query is explicit follow-up phrase
        2. Session exists and not expired
    
    Returns:
        Session data if valid follow-up, None otherwise
    
    Example:
        User: "I want food" → creates session
        User: "show options" → returns session (valid)
        (5 min later)
        User: "show options" → returns None (expired)
    """
    # Check if explicit follow-up phrase
    if not session_is_followup_query(user_input):
        return None
    
    # Try to get valid session
    session = get_session(user_id)
    
    if session:
        print(f"[FOLLOWUP] Valid follow-up detected: {user_input}")
        return session
    else:
        print(f"[FOLLOWUP] Follow-up phrase but no valid session: {user_input}")
        return None


def rewrite_followup_query(
    user_input: str,
    session: Dict[str, Any]
) -> str:
    """
    Rewrite follow-up query using session context.
    
    Args:
        user_input: Original query ("show options")
        session: Valid session data
    
    Returns:
        Rewritten query ("food options in terminal_3")
    """
    msg = user_input.lower().strip()
    
    intent = session.get("intent")
    location = session.get("location")
    
    if msg in ["show options", "more", "more options", "what else"]:
        if location:
            return f"{intent} options in {location}"
        return f"{intent} options"
    
    # Default: return original
    return user_input


# ============================================
# RECOMMENDATION HANDLING (Clean)
# ============================================

def save_recommendation_to_session(
    user_id: str,
    intent: str,
    rag_results: List[Dict[str, Any]],
    location: Optional[str] = None
) -> None:
    """
    Save RAG results to session store (NOT persistent context).
    
    REPLACES:
        context["selected"] = rag_data[0]
        context["last_results"] = rag_data
    
    WITH:
        save_recommendation_to_session(user_id, intent, rag_data, location)
    
    TTL: 5 minutes
    """
    if not rag_results:
        return
    
    set_session(
        user_id=user_id,
        intent=intent,
        selected=rag_results[0],
        last_results=rag_results,
        location=location
    )
    
    print(f"[RECOMMENDATION] Saved to session: intent={intent}, results={len(rag_results)}")


def get_recommendation_from_session(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get recommendation from session store.
    
    REPLACES:
        selected = context.get("selected")
        last_results = context.get("last_results")
    
    WITH:
        session = get_recommendation_from_session(user_id)
        if session:
            selected = session["selected"]
            last_results = session["last_results"]
    
    Returns:
        Session data if valid, None if expired
    """
    return get_session(user_id)


def resolve_destination_from_session(
    msg: str,
    user_id: str
) -> Optional[str]:
    """
    Resolve destination from session cache (for "navigate to it" commands).
    
    REPLACES:
        selected = context.get("selected")
        if selected:
            return selected.get("name")
    
    WITH:
        destination = resolve_destination_from_session(msg, user_id)
    
    Returns:
        Destination name if session valid, None otherwise
    """
    # Check for "navigate to it" style commands
    msg_lower = msg.lower().strip()
    
    if any(phrase in msg_lower for phrase in [
        "navigate there",
        "take me there",
        "go there",
        "navigate to it",
        "take me to it",
        "directions",
    ]):
        session = get_session(user_id)
        if session and session.get("selected"):
            destination = session["selected"].get("name")
            print(f"[DESTINATION] Resolved from session: {destination}")
            return destination
    
    return None


def resolve_option_from_session(
    msg: str,
    user_id: str
) -> Optional[Dict[str, Any]]:
    """
    Resolve "option N" from session cache.
    
    REPLACES:
        option_match = re.search(r"option\s+(\d+)", msg)
        if option_match:
            idx = int(option_match.group(1)) - 1
            last_results = context.get("last_results", [])
            if 0 <= idx < len(last_results):
                return last_results[idx]
    
    WITH:
        result = resolve_option_from_session(msg, user_id)
    
    Returns:
        Selected result if valid, None otherwise
    """
    import re
    
    option_match = re.search(r"option\s+(\d+)", msg.lower())
    if not option_match:
        return None
    
    idx = int(option_match.group(1)) - 1  # 1-indexed → 0-indexed
    
    session = get_session(user_id)
    if not session:
        print(f"[OPTION] No valid session for option selection")
        return None
    
    last_results = session.get("last_results", [])
    
    if 0 <= idx < len(last_results):
        result = last_results[idx]
        print(f"[OPTION] Resolved option {idx + 1}: {result.get('name')}")
        return result
    else:
        print(f"[OPTION] Invalid option index: {idx + 1} (only {len(last_results)} results)")
        return None


# ============================================
# NAVIGATION HANDLING (Clean)
# ============================================

def save_navigation_to_session(
    user_id: str,
    start: str,
    end: str,
    nav_data: Dict[str, Any]
) -> None:
    """
    Save navigation to session store (NOT persistent context).
    
    REPLACES:
        context["mode"] = "navigation"
        context["destination"] = end
    
    WITH:
        save_navigation_to_session(user_id, start, end, nav_data)
    
    TTL: 15 minutes
    """
    set_navigation(
        user_id=user_id,
        start=start,
        end=end,
        route_data=nav_data
    )
    
    print(f"[NAVIGATION] Saved to session: {start} → {end}")


def get_active_navigation(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get active navigation from session store.
    
    REPLACES:
        if context.get("mode") == "navigation":
            ...
    
    WITH:
        nav = get_active_navigation(user_id)
        if nav:
            ...
    
    Returns:
        Navigation data if active, None otherwise
    """
    return get_navigation(user_id)


# ============================================
# INTENT HANDLING (Clean)
# ============================================

def detect_intent_with_session_context(
    message: str,
    user_id: str
) -> str:
    """
    Detect intent with session context awareness.
    
    CRITICAL: Only reuse intent from session if:
        1. Query is explicit follow-up
        2. Session exists and not expired
    
    Otherwise: Fresh intent detection
    
    Args:
        message: User message
        user_id: User identifier
    
    Returns:
        Detected intent
    """
    # Check if follow-up
    if session_is_followup_query(message):
        session = get_session(user_id)
        if session:
            intent = session.get("intent")
            print(f"[INTENT] Reusing from session: {intent}")
            return intent
    
    # Fresh detection
    from app.services.orchestrator import detect_intent
    intent = detect_intent(message)
    print(f"[INTENT] Fresh detection: {intent}")
    return intent


def invalidate_session_on_new_intent(
    user_id: str,
    new_intent: str
) -> None:
    """
    Invalidate session if user switches intent.
    
    Example:
        Session has intent="food"
        User says "I want coffee" (new_intent="coffee")
        → Invalidate old session
    
    Args:
        user_id: User identifier
        new_intent: Newly detected intent
    """
    invalidate_session_if_new_intent(user_id, new_intent)


# ============================================
# RESPONSE BUILDING (Clean)
# ============================================

def build_clean_response(
    response_type: str,
    intent: str,
    message: str,
    data: Dict[str, Any],
    user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build response WITHOUT ephemeral fields in context.
    
    CRITICAL: The returned context should ONLY have persistent fields.
    
    Args:
        response_type: "recommendation" | "navigation" | "general"
        intent: Current intent (NOT persisted)
        message: Response message
        data: Response data
        user_context: Persistent user context
    
    Returns:
        Clean response dict
    """
    from app.services.context_persistence import prepare_for_persistence
    
    # Clean context (remove ephemeral fields)
    clean_context = prepare_for_persistence(user_context)
    
    return {
        "type": response_type,
        "intent": intent,  # Returned in response but NOT in context
        "message": message,
        "data": data,
        "context": clean_context,  # CLEAN - no ephemeral fields
    }


# ============================================
# MIGRATION HELPER
# ============================================

def migrate_legacy_context_to_session(
    user_id: str,
    legacy_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Migrate legacy context with ephemeral fields to new architecture.
    
    This extracts ephemeral fields and moves them to session store.
    
    Args:
        user_id: User identifier
        legacy_context: Old context with ephemeral fields
    
    Returns:
        Clean persistent context
    """
    from app.core.session import migrate_from_persistent_context
    from app.services.context_persistence import clean_legacy_context
    
    # Migrate to session store
    migrate_from_persistent_context(user_id, legacy_context)
    
    # Clean persistent context
    clean_context = clean_legacy_context(legacy_context)
    
    return clean_context
