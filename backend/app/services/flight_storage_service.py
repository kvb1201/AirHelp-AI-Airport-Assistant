"""
Service for managing flight data persistence and queries.
Works offline with JSON file storage.
"""

from typing import Any, Dict, List
from app.core.context.state_manager import StateManager


def store_flight_details(
    user_id: str,
    flight_number: str,
    boarding_time: str,
    departure_time: str,
    terminal: str = "T2",
    gate: str = None,
) -> Dict[str, Any]:
    """
    Store flight details for a user.
    
    Args:
        user_id: Unique user identifier
        flight_number: Flight code (e.g., "AI 143")
        boarding_time: Time when boarding closes (e.g., "10:35")
        departure_time: Flight departure time (e.g., "11:20")
        terminal: Terminal number (default: "T2")
        gate: Gate number (optional)
    
    Returns:
        Updated user context
    """
    patch = {
        "flight_number": flight_number,
        "boarding_time": boarding_time,
        "departure_time": departure_time,
        "terminal": terminal,
    }
    
    if gate:
        patch["gate"] = gate
    
    return StateManager.merge(user_id, patch)


def get_user_flight(user_id: str) -> Dict[str, Any] | None:
    """
    Get flight details for a specific user.
    
    Returns:
        User context with flight details, or None if no flight stored
    """
    context = StateManager.get(user_id)
    
    if not context.get("flight_number"):
        return None
    
    return context


def get_all_active_flights() -> List[Dict[str, Any]]:
    """
    Get all users with active flight bookings.
    Useful for background alert service to check all flights.
    
    Returns:
        List of user contexts that have flight_number set
    """
    all_users = StateManager.list_all_users()
    
    active_flights = [
        user_ctx for user_ctx in all_users.values()
        if user_ctx.get("flight_number") and user_ctx.get("departure_time")
    ]
    
    return active_flights


def clear_user_flight(user_id: str) -> None:
    """Clear flight details for a user (but keep location context)."""
    context = StateManager.get(user_id)
    
    # Remove flight-related fields
    for key in ["flight_number", "boarding_time", "departure_time", "gate"]:
        context.pop(key, None)
    
    # Merge back to remove these keys
    StateManager.merge(user_id, {
        "flight_number": None,
        "boarding_time": None,
        "departure_time": None,
        "gate": None,
    })


def list_all_users() -> Dict[str, Dict[str, Any]]:
    """Get all stored users (for debugging/analytics)."""
    return StateManager.list_all_users()
