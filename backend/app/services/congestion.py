"""
Offline-first congestion hints for walking routes.

- Uses time-of-day + optional “busy terminal” to add **extra minutes** on edges that touch a
  `security` node (queue / screening variability), not live crowd counts.
- Optional `congestion_overlay.json` (rebuilt from nightly telemetry jobs) adds a flat boost.

UI should present totals as **estimates with bands**, not exact queue lengths.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from zoneinfo import ZoneInfo

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_OVERLAY_PATH = _DATA_DIR / "congestion_overlay.json"


@dataclass(frozen=True)
class SecurityExtras:
    """Per security-touching edge: extra queue / screening minutes (integer, conservative)."""

    low: int
    mid: int
    high: int


def load_overlay_security_boost() -> int:
    """Minutes added to each security edge mid/low/high from published overlay (nightly job)."""
    try:
        raw = json.loads(_OVERLAY_PATH.read_text(encoding="utf-8"))
        v = int(raw.get("security_extra_boost_minutes", 0))
        return max(0, min(v, 30))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def security_extras_for_context(*, local_hour: int, busy_terminal: bool) -> SecurityExtras:
    """
    `local_hour`: 0–23, ideally terminal-local (client clock). Drives rush vs quiet priors.
    """
    h = int(local_hour) % 24
    # Peak-ish: early international bank, evening departures (schematic buckets for BOM T2).
    rush = busy_terminal or (5 <= h <= 10) or (17 <= h <= 22)
    elevated = not rush and ((11 <= h <= 14) or (15 <= h <= 16))

    if rush:
        low, mid, high = 2, 6, 14
    elif elevated:
        low, mid, high = 1, 4, 10
    else:
        low, mid, high = 0, 2, 7

    if busy_terminal and not rush:
        mid += 2
        high += 3

    b = load_overlay_security_boost()
    return SecurityExtras(low=low + b, mid=mid + b, high=high + b)


def default_terminal_local_hour() -> int:
    """When the client does not send `local_hour`, assume Asia/Kolkata (CSMIA)."""
    return datetime.now(ZoneInfo("Asia/Kolkata")).hour


def path_time_bands_minutes(
    node_ids: Iterable[str],
    *,
    edges_base: list[tuple[str, str, int]],
    nodes: dict[str, Any],
    extras: SecurityExtras,
) -> tuple[int, int, int, int]:
    """
    For a fixed node sequence, sum base walk minutes plus low/mid/high security extras per edge.
    Returns (low_total, mid_total, high_total, security_edge_count).
    """
    base_map: dict[tuple[str, str], int] = {}
    for a, b, m in edges_base:
        base_map[(a, b)] = int(m)
        base_map[(b, a)] = int(m)

    low = mid = high = 0
    sec_edges = 0
    for u, v in zip(node_ids, node_ids[1:]):
        om = base_map.get((u, v), 0)
        ku = nodes.get(u, {}).get("kind")
        kv = nodes.get(v, {}).get("kind")
        is_sec = ku == "security" or kv == "security"
        if is_sec:
            sec_edges += 1
        low += om + (extras.low if is_sec else 0)
        mid += om + (extras.mid if is_sec else 0)
        high += om + (extras.high if is_sec else 0)

    return low, mid, high, sec_edges


def congestion_public_block(
    *,
    local_hour: int,
    busy_terminal: bool,
    extras: SecurityExtras,
    security_edges_on_route: int,
) -> dict[str, Any]:
    return {
        "mode": "estimate",
        "local_hour_used": int(local_hour) % 24,
        "busy_terminal": bool(busy_terminal),
        "security_edges_on_route": int(security_edges_on_route),
        "security_extra_minutes_per_edge": {"low": extras.low, "mid": extras.mid, "high": extras.high},
        "disclaimer": "",
    }
