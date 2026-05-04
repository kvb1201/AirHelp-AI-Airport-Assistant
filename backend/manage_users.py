"""
Utility script to view, manage and debug stored user flight data.
Run: python backend/manage_users.py
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from app.services.flight_storage_service import (
    list_all_users,
    get_all_active_flights,
)


def format_user(user_id: str, user_data: dict) -> str:
    """Format user data for display."""
    lines = [f"\n👤 User: {user_id}"]
    lines.append(f"   Created: {user_data.get('created_at', 'N/A')}")
    lines.append(f"   Updated: {user_data.get('updated_at', 'N/A')}")
    
    if user_data.get("flight_number"):
        lines.append(f"   ✈️  Flight: {user_data['flight_number']}")
        lines.append(f"      Boarding: {user_data.get('boarding_time', 'N/A')}")
        lines.append(f"      Departure: {user_data.get('departure_time', 'N/A')}")
        lines.append(f"      Terminal: {user_data.get('terminal', 'N/A')}")
        lines.append(f"      Gate: {user_data.get('gate', 'N/A')}")
    else:
        lines.append("   (No flight booked)")
    
    if user_data.get("location"):
        lines.append(f"   📍 Location: {user_data['location']}")
    
    return "\n".join(lines)


def main():
    """Display all users and their flight data."""
    all_users = list_all_users()
    
    print("\n" + "="*60)
    print("📊 USER FLIGHT DATA - OFFLINE JSON STORAGE")
    print("="*60)
    
    if not all_users:
        print("\n⚠️  No users in storage yet.")
        return
    
    # Display all users
    for user_id, user_data in all_users.items():
        print(format_user(user_id, user_data))
    
    # Summary
    print(f"\n\n📈 SUMMARY:")
    print(f"   Total users: {len(all_users)}")
    
    active_flights = get_all_active_flights()
    print(f"   Users with active flights: {len(active_flights)}")
    
    # Show which flights need alerts
    print(f"\n⏰ UPCOMING ALERTS:")
    for flight in active_flights:
        user_id = flight.get("user_id", "unknown")
        flight_num = flight.get("flight_number", "unknown")
        departure = flight.get("departure_time", "unknown")
        print(f"   - {user_id}: {flight_num} departing at {departure}")
    
    # Also show raw JSON for reference
    print(f"\n\n📋 RAW JSON DATA:")
    print(json.dumps(all_users, indent=2))
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
