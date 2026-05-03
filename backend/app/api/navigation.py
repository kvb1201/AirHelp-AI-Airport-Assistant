# backend/app/api/navigation.py

from fastapi import APIRouter, Query

from app.services.navigation_service import get_route

router = APIRouter()


@router.get("/navigate")
def navigate(
    start: str = Query(..., description="Starting location"),
    end: str = Query(..., description="Destination location")
):
    """
    Navigation endpoint (mainly for testing/debugging).
    Returns structured route data.
    """

    route = get_route(start, end)

    return {
        "type": "navigation",
        "intent": "navigation",
        "message": f"Route from {start} to {end}",

        "data": {
            "navigation": route
        },

        "context": {}
    }