"""
Ephemeral Session Management

This module provides in-memory session storage with TTL expiry
to prevent conversational contamination.
"""

from app.core.session.session_store import (
    # Session management
    get_session,
    set_session,
    clear_session,
    invalidate_session_if_new_intent,
    
    # Navigation management
    get_navigation,
    set_navigation,
    complete_navigation,
    cancel_navigation,
    clear_navigation,
    
    # Follow-up detection
    is_followup_query,
    
    # Utilities
    cleanup_expired_sessions,
    get_store_stats,
    migrate_from_persistent_context,
)

__all__ = [
    "get_session",
    "set_session",
    "clear_session",
    "invalidate_session_if_new_intent",
    "get_navigation",
    "set_navigation",
    "complete_navigation",
    "cancel_navigation",
    "clear_navigation",
    "is_followup_query",
    "cleanup_expired_sessions",
    "get_store_stats",
    "migrate_from_persistent_context",
]
