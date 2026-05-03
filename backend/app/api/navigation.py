from fastapi import APIRouter
from app.services.navigation_service import get_shortest_path

router = APIRouter()

@router.get("/navigation/route")
def get_route(start_node: str, end_node: str):
    # Calculates graph-based path
    path = get_shortest_path(start_node, end_node)
    return {"path": path}
