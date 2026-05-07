"""
Ephemeral Session Store for Airport AI Assistant

PURPOSE:
    Eliminate conversational contamination by separating:
    - Persistent user profile (users.json)
    - Ephemeral orchestration state (in-memory with TTL)

PROBLEM SOLVED:
    Before: intent, mode, selected, last_results persisted forever in users.json
    After: These fields expire automatically after 5-15 minutes

ARCHITECTURE:
    - SESSION_STORE: Recommendation cache (5 min TTL)
    - NAVIGATION_STORE: Active navigation (15 min TTL)
    - Auto-expiry on access
    - No Redis required (hackathon-grade simplicity)

CRITICAL:
    This module prevents stale orchestration state from contaminating
    future unrelated prompts.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# ============================================
# IN-MEMORY STORES
# ============================================

# Recommendation session cache (5 min TTL)
SESSION_STORE: Dict[str, Dict[str, Any]] = {}

# Active navigation sessions (15 min TTL)
NAVIGATION_STORE: Dict[str, Dict[str, Any]] = {}

# ============================================
# TTL CONFIGURATION
# ============================================

RECOMMENDATION_TTL_SECONDS = 300  # 5 minutes
NAVIGATION_TTL_SECONDS = 900      # 15 minutes

# ============================================
# FOLLOW-UP DETECTION
# ============================================

FOLLOWUP_PHRASES = {
    # Show more options
    "show options",
    "more",
    "more options",
    "what else",
    "anything else",
    "other options",
    
    # Select option by number
    "option 1",
    "option 2",
    "option 3",
    "option 4",
    "option 5",
    
    # Navigate to selected
    "navigate there",
    "take me there",
    "go there",
    "navigate to it",
    "take me to it",
    "directions",
    "how do i get there",
}


def is_followup_query(message: str) -> bool:
    """
    Detect if message is a follow-up to previous recommendation.
    
    CRITICAL: Only return True if message is EXPLICITLY a follow-up phrase.
    
    Examples:
        "show options" → True
        "option 2" → True
        "navigate there" → True
        "hello" → False
        "I want food" → False
        "suggest lounges" → False
    """
    msg = message.lower().strip()
    
    # Exact phrase match
    if msg in FOLLOWUP_PHRASES:
        return True
    
    # Option N pattern
    if msg.startswith("option ") and len(msg.split()) == 2:
        try:
            int(msg.split()[1])
            return True
        except ValueError:
            pass
    
    return False


# ============================================
# SESSION STORE (Recommendation Cache)
# ============================================

def get_session(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get recommendation session if exists and not expired.
    
    Returns:
        Session data if valid, None if expired or doesn't exist
    
    Side effects:
        Auto-deletes expired sessions
    """
    if user_id not in SESSION_STORE:
        return None
    
    session = SESSION_STORE[user_id]
    
    # Check expiry
    if time.time() > session.get("expires_at", 0):
        # Expired - delete and return None
        del SESSION_STORE[user_id]
        print(f"[SESSION] Expired and deleted session for {user_id}")
        return None
    
    print(f"[SESSION] Valid session found for {user_id}")
    return session


def set_session(
    user_id: str,
    intent: str,
    selected: Dict[str, Any],
    last_results: List[Dict[str, Any]],
    location: Optional[str] = None
) -> None:
    """
    Create or update recommendation session.
    
    Args:
        user_id: User identifier
        intent: Current intent (food, coffee, etc.)
        selected: Best recommendation
        last_results: All recommendations (for "option N")
        location: User location context
    
    TTL: 5 minutes
    """
    now = time.time()
    
    SESSION_STORE[user_id] = {
        "intent": intent,
        "selected": selected,
        "last_results": last_results,
        "location": location,
        "created_at": now,
        "expires_at": now + RECOMMENDATION_TTL_SECONDS,
    }
    
    print(f"[SESSION] Created session for {user_id}: intent={intent}, results={len(last_results)}")


def clear_session(user_id: str) -> None:
    """
    Explicitly clear recommendation session.
    
    Use cases:
        - User starts new intent (invalidates old cache)
        - User explicitly cancels
    """
    if user_id in SESSION_STORE:
        del SESSION_STORE[user_id]
        print(f"[SESSION] Cleared session for {user_id}")


def invalidate_session_if_new_intent(user_id: str, new_intent: str) -> None:
    """
    Invalidate session if user switches to different intent.
    
    Example:
        Session has intent="food"
        User says "I want coffee" (new_intent="coffee")
        → Invalidate old session
    """
    session = get_session(user_id)
    
    if session and session.get("intent") != new_intent:
        print(f"[SESSION] Intent changed: {session.get('intent')} → {new_intent}, invalidating")
        clear_session(user_id)


# ============================================
# NAVIGATION STORE
# ============================================

def get_navigation(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get active navigation session if exists and not expired.
    
    Returns:
        Navigation data if active, None if expired or doesn't exist
    
    Side effects:
        Auto-deletes expired navigation
    """
    if user_id not in NAVIGATION_STORE:
        return None
    
    nav = NAVIGATION_STORE[user_id]
    
    # Check expiry
    if time.time() > nav.get("expires_at", 0):
        # Expired - delete and return None
        del NAVIGATION_STORE[user_id]
        print(f"[NAVIGATION] Expired and deleted navigation for {user_id}")
        return None
    
    # Check if completed or cancelled
    if nav.get("status") in ["completed", "cancelled"]:
        print(f"[NAVIGATION] Navigation {nav.get('status')} for {user_id}")
        return None
    
    print(f"[NAVIGATION] Active navigation found for {user_id}")
    return nav


def set_navigation(
    user_id: str,
    start: str,
    end: str,
    route_data: Dict[str, Any]
) -> None:
    """
    Create active navigation session.
    
    Args:
        user_id: User identifier
        start: Start location
        end: Destination
        route_data: Navigation route details
    
    TTL: 15 minutes
    """
    now = time.time()
    
    NAVIGATION_STORE[user_id] = {
        "active": True,
        "status": "active",
        "start": start,
        "end": end,
        "route": route_data,
        "created_at": now,
        "expires_at": now + NAVIGATION_TTL_SECONDS,
    }
    
    print(f"[NAVIGATION] Created navigation for {user_id}: {start} → {end}")


def complete_navigation(user_id: str) -> None:
    """
    Mark navigation as completed.
    
    This prevents the navigation from being reused.
    """
    if user_id in NAVIGATION_STORE:
        NAVIGATION_STORE[user_id]["status"] = "completed"
        NAVIGATION_STORE[user_id]["active"] = False
        print(f"[NAVIGATION] Completed navigation for {user_id}")


def cancel_navigation(user_id: str) -> None:
    """
    Cancel active navigation.
    """
    if user_id in NAVIGATION_STORE:
        NAVIGATION_STORE[user_id]["status"] = "cancelled"
        NAVIGATION_STORE[user_id]["active"] = False
        print(f"[NAVIGATION] Cancelled navigation for {user_id}")


def clear_navigation(user_id: str) -> None:
    """
    Explicitly clear navigation session.
    """
    if user_id in NAVIGATION_STORE:
        del NAVIGATION_STORE[user_id]
        print(f"[NAVIGATION] Cleared navigation for {user_id}")


# ============================================
# CLEANUP UTILITIES
# ============================================

def cleanup_expired_sessions() -> None:
    """
    Cleanup all expired sessions and navigation.
    
    Call this periodically (e.g., every minute) to prevent memory leaks.
    """
    now = time.time()
    
    # Cleanup expired recommendation sessions
    expired_sessions = [
        user_id for user_id, session in SESSION_STORE.items()
        if now > session.get("expires_at", 0)
    ]
    
    for user_id in expired_sessions:
        del SESSION_STORE[user_id]
    
    if expired_sessions:
        print(f"[CLEANUP] Removed {len(expired_sessions)} expired sessions")
    
    # Cleanup expired navigation
    expired_nav = [
        user_id for user_id, nav in NAVIGATION_STORE.items()
        if now > nav.get("expires_at", 0)
    ]
    
    for user_id in expired_nav:
        del NAVIGATION_STORE[user_id]
    
    if expired_nav:
        print(f"[CLEANUP] Removed {len(expired_nav)} expired navigations")


def get_store_stats() -> Dict[str, Any]:
    """
    Get statistics about current store state.
    
    Useful for monitoring and debugging.
    """
    return {
        "active_sessions": len(SESSION_STORE),
        "active_navigations": len(NAVIGATION_STORE),
        "sessions": list(SESSION_STORE.keys()),
        "navigations": list(NAVIGATION_STORE.keys()),
    }


# ============================================
# MIGRATION HELPER
# ============================================

def migrate_from_persistent_context(user_id: str, old_context: Dict[str, Any]) -> None:
    """
    Migrate old persistent context to new ephemeral stores.
    
    This is a one-time migration helper for existing users.json data.
    
    IMPORTANT: After migration, remove these fields from users.json:
        - intent
        - mode
        - selected
        - last_results
        - destination
    """
    # Migrate recommendation cache
    if old_context.get("selected") and old_context.get("last_results"):
        set_session(
            user_id=user_id,
            intent=old_context.get("intent", "unknown"),
            selected=old_context["selected"],
            last_results=old_context["last_results"],
            location=old_context.get("source")
        )
        print(f"[MIGRATION] Migrated recommendation cache for {user_id}")
    
    # Migrate navigation state
    if old_context.get("mode") == "navigation" and old_context.get("destination"):
        # Create placeholder navigation (we don't have full route data)
        set_navigation(
            user_id=user_id,
            start=old_context.get("source", "unknown"),
            end=old_context.get("destination"),
            route_data={"migrated": True}
        )
        print(f"[MIGRATION] Migrated navigation state for {user_id}")
