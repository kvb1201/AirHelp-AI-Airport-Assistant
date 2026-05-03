# backend/app/api/navigation.py

from fastapi import APIRouter, Query

from app.services.navigation_service import get_route

router = APIRouter()


@router.get("/navigate")
def navigate(
    start: str = Query(..., description="Start zone (e.g. entrance, security, gate_a1)"),
    end: str = Query(..., description="Goal zone or gate (e.g. gate_b12, food_court)"),
    local_hour: int | None = Query(
        None,
        ge=0,
        le=23,
        description="Client local hour (0–23) for time-of-day congestion priors; omit to use Asia/Kolkata server clock.",
    ),
    busy_terminal: bool = Query(
        False,
        description="User / device flag: heavier assumed queues on security-touching edges.",
    ),
):
    """
    Debug / mobile map: graph shortest path in minutes between two semantic nodes.
    """
    route = get_route(start, end, local_hour=local_hour, busy_terminal=busy_terminal)
    ok = route.get("ok", False)
    if ok:
        sj = route.get("simple_journey") or {}
        msg = sj.get("subtitle") or f"About {route.get('total_time_minutes')} min walk"
    else:
        msg = route.get("hint") or route.get("error", "navigation error")

    return {
        "type": "navigation",
        "intent": "navigation",
        "message": msg,
        "data": {"navigation": route},
        "context": {},
    }