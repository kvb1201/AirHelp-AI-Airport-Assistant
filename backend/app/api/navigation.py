# backend/app/api/navigation.py

from fastapi import APIRouter, Query

from app.services.navigation_knowledge import NavigationKnowledgeIntegrator
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
    Graph shortest path with turn-by-turn directions, distances in meters,
    and nearby landmarks for precise wayfinding.
    """
    route = get_route(start, end, local_hour=local_hour, busy_terminal=busy_terminal)
    ok = route.get("ok", False)
    if ok:
        sj = route.get("simple_journey") or {}
        summary = route.get("route_summary") or {}
        distance_str = summary.get("total_distance_formatted", "")
        msg = f"{sj.get('subtitle', '')} — {distance_str}, about {route.get('total_time_minutes')} min walk"
    else:
        msg = route.get("hint") or route.get("error", "navigation error")

    return {
        "type": "navigation",
        "intent": "navigation",
        "message": msg,
        "data": {"navigation": route},
        "context": {},
    }


@router.get("/contextual")
def contextual_navigation(
    start: str = Query(..., description="Start node ID"),
    end: str = Query(..., description="Destination node ID"),
    query: str | None = Query(None, description="User query for context"),
):
    """
    Get navigation with full contextual information including:
    - Turn-by-turn directions with distances in meters
    - Nearby facilities and shops at start and destination
    - Knowledge base context relevant to the query
    """
    integrator = NavigationKnowledgeIntegrator()
    
    result = integrator.get_contextual_directions(
        from_node_id=start,
        to_node_id=end,
        user_query=query,
    )
    
    return {
        "type": "contextual_navigation",
        "intent": "navigation",
        "data": result,
    }


@router.get("/location/{node_id}")
def location_context(node_id: str):
    """
    Get detailed context about a specific location including:
    - Node information
    - Nearby facilities (within 100m)
    - Nearby shops (within 100m)
    """
    integrator = NavigationKnowledgeIntegrator()
    context = integrator.enrich_node_with_context(node_id)
    
    return {
        "type": "location_context",
        "data": context,
    }


@router.get("/search")
def search_locations(q: str = Query(..., description="Search query")):
    """
    Search for locations by name across:
    - Graph nodes (corridors, gates, facilities)
    - Airport facilities
    - Shops and dining
    """
    integrator = NavigationKnowledgeIntegrator()
    results = integrator.search_location_by_name(q)
    
    return {
        "type": "location_search",
        "query": q,
        "results": results,
        "count": len(results),
    }