"""
Lightweight offline alert scheduler.

Runs an async loop that checks `get_all_active_flights()` every minute
and persists sent nudges to avoid duplicate alerts. Alerts are appended
to `backend/app/data/alerts.log` and the user's `alerts_sent` list is
updated in `users.json`.

This runs entirely offline (no external services) and is suitable for
local/demo use.
"""
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any

from app.services.flight_storage_service import get_all_active_flights
from app.core.context.state_manager import StateManager
from app.services.orchestrator import _parse_time_to_minutes

ROOT = Path(__file__).resolve().parents[3]
ALERTS_LOG = ROOT / "backend" / "app" / "data" / "alerts.log"


def _ensure_alerts_log():
    if not ALERTS_LOG.exists():
        ALERTS_LOG.write_text("", encoding="utf-8")


def _append_alert_log(line: str) -> None:
    _ensure_alerts_log()
    ts = datetime.now().astimezone().isoformat()
    ALERTS_LOG.write_text(ALERTS_LOG.read_text(encoding="utf-8") + f"[{ts}] {line}\n", encoding="utf-8")


def _compute_nudge_minutes_for_flight(flight: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return list of events with 'label' and 'minutes' (minutes since midnight).

    Mirrors logic in `_build_time_nudges` from orchestrator.
    """
    boarding_time = flight.get("boarding_time")
    departure_time = flight.get("departure_time")

    boarding_minutes = _parse_time_to_minutes(boarding_time)
    departure_minutes = _parse_time_to_minutes(departure_time)

    if boarding_minutes is None and departure_minutes is not None:
        boarding_minutes = max(departure_minutes - 45, 0)
    elif departure_minutes is None and boarding_minutes is not None:
        departure_minutes = boarding_minutes + 45

    if boarding_minutes is None:
        boarding_minutes = 0
    if departure_minutes is None:
        departure_minutes = boarding_minutes + 45

    events = [
        {"label": "Head to security", "minutes": max(departure_minutes - 120, 0)},
        {"label": "Go to gate", "minutes": max(boarding_minutes - 45, 0)},
        {"label": "Final call", "minutes": max(boarding_minutes - 10, 0)},
    ]

    return events


async def _scheduler_loop(poll_interval_seconds: int = 60):
    tz_offset = timedelta(0)
    try:
        # Attempt to use local timezone offset
        tz_offset = datetime.now().astimezone().utcoffset() or timedelta(0)
    except Exception:
        tz_offset = timedelta(0)

    while True:
        try:
            now = datetime.now().astimezone()
            now_minutes = now.hour * 60 + now.minute

            flights = get_all_active_flights()
            for user_ctx in flights:
                user_id = user_ctx.get("user_id") or user_ctx.get("user_id")
                if not user_id:
                    continue

                events = _compute_nudge_minutes_for_flight(user_ctx)

                sent: List[str] = user_ctx.get("alerts_sent") or []

                for ev in events:
                    label = ev["label"]
                    ev_minutes = ev["minutes"]

                    # If event time has passed and not yet sent, append alert
                    if now_minutes >= ev_minutes and label not in sent:
                        # Compose message and persist
                        flight_num = user_ctx.get("flight_number", "your flight")
                        message = f"Alert for {user_id}: {flight_num} · {label} (scheduled at {ev_minutes // 60:02d}:{ev_minutes % 60:02d})"
                        _append_alert_log(message)

                        # Mark as sent in user's context
                        sent.append(label)
                        StateManager.merge(user_id, {"alerts_sent": sent})

        except Exception as exc:
            _append_alert_log(f"Scheduler error: {exc}")

        await asyncio.sleep(poll_interval_seconds)


def start_alert_scheduler(loop=None):
    """Start the scheduler as an asyncio task in the provided loop (or current loop)."""
    if loop is None:
        loop = asyncio.get_event_loop()
    loop.create_task(_scheduler_loop())
