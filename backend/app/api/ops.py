"""Operator live ops: REST + WebSocket broadcast."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Request, WebSocket
from pydantic import BaseModel, Field

from app.config import AIRHELP_OPERATOR_TOKEN
from app.services import operational_state_service as ops

router = APIRouter()


def _operator_token() -> str:
    return AIRHELP_OPERATOR_TOKEN


def _require_operator(request: Request) -> None:
    expected = _operator_token()
    if not expected:
        return
    got = (request.headers.get("x-operator-token") or "").strip()
    if got != expected:
        raise HTTPException(status_code=401, detail="Missing or invalid X-Operator-Token")


def _ws_token_ok(token: str | None) -> bool:
    expected = _operator_token()
    if not expected:
        return True
    return (token or "").strip() == expected


class GlobalNoticeBody(BaseModel):
    title: str | None = None
    body: str | None = None


class BulletinBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=2000)
    severity: Literal["info", "warning", "critical"] = "info"


class FlightOverrideBody(BaseModel):
    flight: str = Field(..., min_length=2, max_length=16)
    gate: str | None = Field(None, max_length=32)
    delay_minutes: int | None = Field(None, ge=0, le=1440)
    status: str | None = Field(None, max_length=120)
    note: str | None = Field(None, max_length=500)


@router.get("/ops/state")
async def get_ops_state():
    return ops.get_state()


@router.post("/ops/global-notice")
async def post_global_notice(request: Request, body: GlobalNoticeBody):
    _require_operator(request)
    return await ops.set_global_notice(body.title, body.body)


@router.post("/ops/bulletin")
async def post_bulletin(request: Request, body: BulletinBody):
    _require_operator(request)
    return await ops.add_bulletin(body.title, body.body, body.severity)


@router.delete("/ops/bulletin/{bulletin_id}")
async def delete_bulletin(bulletin_id: str, request: Request):
    _require_operator(request)
    return await ops.remove_bulletin(bulletin_id)


@router.post("/ops/flight-override")
async def post_flight_override(request: Request, body: FlightOverrideBody):
    _require_operator(request)
    try:
        return await ops.upsert_flight_override(
            body.flight,
            gate=body.gate,
            delay_minutes=body.delay_minutes,
            status=body.status,
            note=body.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/ops/flight-override/{flight}")
async def delete_flight_override(flight: str, request: Request):
    _require_operator(request)
    return await ops.remove_flight_override(flight)


@router.websocket("/ops/ws")
async def ops_websocket(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not _ws_token_ok(token):
        await websocket.close(code=4401)
        return
    await ops.register_ws(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await ops.unregister_ws(websocket)
