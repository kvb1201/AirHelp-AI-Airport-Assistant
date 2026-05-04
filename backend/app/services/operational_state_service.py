"""
Airport operator–controlled live state (gate changes, delays, bulletins).

- Persisted to ``app/data/operational_state.json`` (gitignored).
- All connected WebSocket clients receive ``ops_updated`` after each mutation.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import WebSocket

_STATE_LOCK = asyncio.Lock()
_WS_LOCK = asyncio.Lock()
_CONNECTIONS: list[WebSocket] = []

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "operational_state.json"


def get_data_path() -> Path:
    return _DATA_PATH

_state: dict[str, Any] = {
    "version": 0,
    "updated_at": None,
    "global_notice": None,
    "bulletins": [],
    "flight_overrides": {},
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_flight_key(flight: str) -> str:
    return (flight or "").strip().upper().replace(" ", "")


def load_from_disk() -> None:
    global _state
    if not _DATA_PATH.is_file():
        return
    try:
        raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "version" in raw:
            _state = {
                "version": int(raw.get("version") or 0),
                "updated_at": raw.get("updated_at"),
                "global_notice": raw.get("global_notice"),
                "bulletins": raw.get("bulletins") if isinstance(raw.get("bulletins"), list) else [],
                "flight_overrides": raw.get("flight_overrides")
                if isinstance(raw.get("flight_overrides"), dict)
                else {},
            }
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass


def _persist_unlocked() -> None:
    _DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _DATA_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(_state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(_DATA_PATH)


async def _persist_and_broadcast() -> dict[str, Any]:
    async with _STATE_LOCK:
        _state["version"] = int(_state.get("version") or 0) + 1
        _state["updated_at"] = _utc_now_iso()
        snapshot = get_state()
        _persist_unlocked()
    await _broadcast({"type": "ops_updated", "state": snapshot})
    return snapshot


def get_state() -> dict[str, Any]:
    """Public JSON snapshot (copy)."""
    return {
        "version": _state.get("version", 0),
        "updated_at": _state.get("updated_at"),
        "global_notice": _state.get("global_notice"),
        "bulletins": list(_state.get("bulletins") or []),
        "flight_overrides": dict(_state.get("flight_overrides") or {}),
    }


def get_brief_for_llm(max_chars: int = 1600) -> str:
    """Compact text for LLM fallback — operator-entered facts only."""
    s = get_state()
    lines: list[str] = []
    gn = s.get("global_notice")
    if isinstance(gn, dict) and (gn.get("title") or gn.get("body")):
        t = str(gn.get("title") or "").strip()
        b = str(gn.get("body") or "").strip()
        lines.append(f"Operator notice{f' ({t})' if t else ''}: {b}".strip())

    for b in (s.get("bulletins") or [])[-12:]:
        if not isinstance(b, dict):
            continue
        sev = str(b.get("severity") or "info")
        title = str(b.get("title") or "").strip()
        body = str(b.get("body") or "").strip()
        if title or body:
            lines.append(f"[{sev}] {title}: {body}".strip())

    fo = s.get("flight_overrides") or {}
    if isinstance(fo, dict):
        for flight, ov in sorted(fo.items()):
            if not isinstance(ov, dict):
                continue
            bits = []
            if ov.get("gate"):
                bits.append(f"gate {ov['gate']}")
            if ov.get("delay_minutes") is not None:
                try:
                    bits.append(f"delay +{int(ov['delay_minutes'])} min")
                except (TypeError, ValueError):
                    bits.append(f"delay {ov['delay_minutes']}")
            if ov.get("status"):
                bits.append(f"status {ov['status']}")
            if ov.get("note"):
                bits.append(str(ov["note"]))
            if bits:
                lines.append(f"Flight {flight}: " + "; ".join(bits))

    out = "\n".join(lines).strip()
    return out[:max_chars] if out else ""


async def register_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    async with _WS_LOCK:
        _CONNECTIONS.append(websocket)
    try:
        await websocket.send_json({"type": "ops_snapshot", "state": get_state()})
    except Exception:
        pass


async def unregister_ws(websocket: WebSocket) -> None:
    async with _WS_LOCK:
        if websocket in _CONNECTIONS:
            _CONNECTIONS.remove(websocket)


async def _broadcast(payload: dict[str, Any]) -> None:
    async with _WS_LOCK:
        conns = list(_CONNECTIONS)
    dead: list[WebSocket] = []
    for ws in conns:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    if dead:
        async with _WS_LOCK:
            for ws in dead:
                if ws in _CONNECTIONS:
                    _CONNECTIONS.remove(ws)


async def set_global_notice(title: str | None, body: str | None) -> dict[str, Any]:
    async with _STATE_LOCK:
        if not (title or body):
            _state["global_notice"] = None
        else:
            _state["global_notice"] = {
                "title": (title or "").strip() or None,
                "body": (body or "").strip() or None,
            }
    return await _persist_and_broadcast()


async def add_bulletin(title: str, body: str, severity: str = "info") -> dict[str, Any]:
    bid = uuid.uuid4().hex[:10]
    item = {
        "id": bid,
        "title": (title or "").strip(),
        "body": (body or "").strip(),
        "severity": severity if severity in ("info", "warning", "critical") else "info",
        "created_at": _utc_now_iso(),
    }
    async with _STATE_LOCK:
        bulletins = list(_state.get("bulletins") or [])
        bulletins.append(item)
        _state["bulletins"] = bulletins[-50:]
    return await _persist_and_broadcast()


async def remove_bulletin(bulletin_id: str) -> dict[str, Any]:
    async with _STATE_LOCK:
        bulletins = [b for b in (_state.get("bulletins") or []) if isinstance(b, dict) and b.get("id") != bulletin_id]
        _state["bulletins"] = bulletins
    return await _persist_and_broadcast()


async def upsert_flight_override(
    flight: str,
    gate: str | None = None,
    delay_minutes: int | None = None,
    status: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    key = _normalize_flight_key(flight)
    if not key:
        raise ValueError("flight required")
    entry: dict[str, Any] = {}
    if gate is not None and str(gate).strip():
        entry["gate"] = str(gate).strip()
    if delay_minutes is not None:
        entry["delay_minutes"] = int(delay_minutes)
    if status is not None and str(status).strip():
        entry["status"] = str(status).strip()
    if note is not None and str(note).strip():
        entry["note"] = str(note).strip()
    async with _STATE_LOCK:
        fo = dict(_state.get("flight_overrides") or {})
        if not entry:
            fo.pop(key, None)
        else:
            fo[key] = {**fo.get(key, {}), **entry} if isinstance(fo.get(key), dict) else entry
        _state["flight_overrides"] = fo
    return await _persist_and_broadcast()


async def remove_flight_override(flight: str) -> dict[str, Any]:
    key = _normalize_flight_key(flight)
    async with _STATE_LOCK:
        fo = dict(_state.get("flight_overrides") or {})
        fo.pop(key, None)
        _state["flight_overrides"] = fo
    return await _persist_and_broadcast()


async def replace_full_state(payload: dict[str, Any]) -> dict[str, Any]:
    """Replace bulletins / flight_overrides / global_notice (used sparingly)."""
    async with _STATE_LOCK:
        if "global_notice" in payload:
            gn = payload.get("global_notice")
            _state["global_notice"] = gn if gn else None
        if "bulletins" in payload and isinstance(payload.get("bulletins"), list):
            _state["bulletins"] = payload["bulletins"][-50:]
        if "flight_overrides" in payload and isinstance(payload.get("flight_overrides"), dict):
            _state["flight_overrides"] = dict(payload["flight_overrides"])
    return await _persist_and_broadcast()
