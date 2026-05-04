"""Test file-based JSON storage for flight details."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.flight_storage_service import (
    store_flight_details,
    get_user_flight,
    get_all_active_flights,
    list_all_users,
)
from app.core.context.state_manager import StateManager


def test_json_storage():
    """Test that flight details are persisted to users.json."""
    
    # Clear test user
    StateManager.clear("test_user_001")
    
    # Store flight details
    user_ctx = store_flight_details(
        user_id="test_user_001",
        flight_number="AI 143",
        boarding_time="10:35",
        departure_time="11:20",
        terminal="T2",
        gate="B12",
    )
    
    print("✓ Stored flight details")
    print(f"  User context: {user_ctx}")
    
    # Retrieve and verify
    retrieved = get_user_flight("test_user_001")
    assert retrieved is not None
    assert retrieved["flight_number"] == "AI 143"
    assert retrieved["boarding_time"] == "10:35"
    assert retrieved["departure_time"] == "11:20"
    assert retrieved["terminal"] == "T2"
    assert retrieved["gate"] == "B12"
    
    print("✓ Retrieved flight details from storage")
    
    # Store another user's flight
    store_flight_details(
        user_id="test_user_002",
        flight_number="BA 286",
        boarding_time="15:20",
        departure_time="16:00",
        terminal="T1",
    )
    
    print("✓ Stored second user's flight")
    
    # Get all active flights
    all_flights = get_all_active_flights()
    assert len(all_flights) >= 2
    
    print(f"✓ Retrieved {len(all_flights)} active flights from storage")
    
    # List all users
    all_users = list_all_users()
    print(f"✓ Total users in storage: {len(all_users)}")
    
    # Verify persistence (simulate server restart by reloading)
    from app.core.context.state_manager import _load_users_db
    reloaded = _load_users_db()
    assert "test_user_001" in reloaded
    assert reloaded["test_user_001"]["flight_number"] == "AI 143"
    
    print("✓ Data persisted to disk (simulated restart)")
    
    # Cleanup
    StateManager.clear("test_user_001")
    StateManager.clear("test_user_002")
    
    print("\n✅ All JSON storage tests passed!")


if __name__ == "__main__":
    test_json_storage()
