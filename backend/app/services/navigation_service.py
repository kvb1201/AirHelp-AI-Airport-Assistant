# backend/app/services/navigation_service.py

def get_route(start: str, query: str):
    """
    Mock navigation engine.
    Later: replace with graph logic.
    """

    return {
        "path": ["security", "corridor_A", "gate_B12"],
        "total_time": 6,
        "steps": [
            "Walk straight from security",
            "Enter Corridor A",
            "Continue to Gate B12"
        ]
    }