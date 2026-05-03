"""Guided step-by-step walking + relocalization API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.guided_navigation_service import build_guided_checkpoints, relocalize

router = APIRouter()


class GuidedCheckpointsBody(BaseModel):
    path: list[str]
    edges: list[dict[str, Any]]


class GuidedRelocalizeBody(BaseModel):
    path: list[str]
    last_confirmed_path_index: int = Field(..., ge=0)
    next_waypoint_path_index: int = Field(..., ge=0)
    observation: str = Field(..., min_length=1, max_length=400)
    local_hour: int | None = Field(None, ge=0, le=23)
    busy_terminal: bool = False


@router.post("/guided-nav/checkpoints")
def post_guided_checkpoints(body: GuidedCheckpointsBody) -> dict[str, Any]:
    """
    Build checkpoint questions along a route path (from /navigate).
    Client sends `path` (ordered node ids) and `edges` from the chosen route option.
    """
    return build_guided_checkpoints(body.path, body.edges)


@router.post("/guided-nav/relocalize")
def post_guided_relocalize(body: GuidedRelocalizeBody) -> dict[str, Any]:
    """
    User did not match the expected checkpoint; they describe what they see (e.g. washroom).
    Returns ranked graph nodes to replan from.
    """
    return relocalize(
        path=body.path,
        last_confirmed_path_index=body.last_confirmed_path_index,
        next_waypoint_path_index=body.next_waypoint_path_index,
        observation=body.observation,
        local_hour=body.local_hour,
        busy_terminal=body.busy_terminal,
    )
