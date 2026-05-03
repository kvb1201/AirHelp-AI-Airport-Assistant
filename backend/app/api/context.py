from fastapi import APIRouter
from app.services.context_service import get_user_context, update_user_context

router = APIRouter()

@router.get("/context/{user_id}")
def get_context(user_id: str):
    return get_user_context(user_id) or {}
