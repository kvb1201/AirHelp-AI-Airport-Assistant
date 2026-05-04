"""
Mumbai T2 gate segregation heuristics (swing gates, domestic / international lean).

Resolves numeric gate references (e.g. ``Gate 52``, ``g45``) to a **routable** graph node
on the L02 walking model (pier tips / retail hubs). This is **not** a substitute for FIDS
or the boarding pass — see ``mumbai_t2_gate_segregation.json`` disclaimers.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.core.graph.airport_data import NODES

_DATA = Path(__file__).resolve().parents[1] / "data" / "mumbai_t2_gate_segregation.json"


@lru_cache(maxsize=1)
def _policy() -> Dict[str, Any]:
    if not _DATA.exists():
        return {}
    try:
        return json.loads(_DATA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _text_flavor(context_lower: str) -> Optional[str]:
    pol = _policy()
    fk = pol.get("flavor_keywords") or {}
    for flavor in ("international", "domestic"):
        for w in fk.get(flavor) or []:
            if w and w in context_lower:
                return flavor
    return None


def _level_goal(context_lower: str) -> Optional[str]:
    pol = _policy()
    lk = pol.get("level_keywords") or {}
    for _lvl, spec in lk.items():
        for pat in spec.get("patterns") or []:
            if pat and pat in context_lower:
                g = spec.get("goal")
                if g and g in NODES:
                    return str(g)
    return None


def _band_goal(num: int) -> Tuple[Optional[str], Optional[str]]:
    pol = _policy()
    for band in pol.get("numeric_bands") or []:
        lo = int(band.get("min", 0))
        hi = int(band.get("max", 999))
        if lo <= num <= hi:
            gid = band.get("goal_node")
            if gid and gid in NODES:
                label = band.get("label")
                disc = band.get("disclaimer")
                note = " — ".join(x for x in (label, disc) if x)
                return str(gid), note
    return None, None


def goal_graph_for_numeric_gate(gate_num: int, context_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Pick a graph goal for a numeric gate (1–99) using policy + optional domestic/intl/L3/L4 words.
    Returns (graph_id, short_advisory) or (None, None).
    """
    if gate_num < 1 or gate_num > 99:
        return None, None

    ctx = (context_text or "").lower()

    lg = _level_goal(ctx)
    if lg:
        pol = _policy()
        summ = pol.get("summary", "")
        return lg, (summ[:280] + "…") if len(summ) > 280 else summ

    flavor = _text_flavor(ctx)

    pol = _policy()
    fg = pol.get("flavor_goal") or {}
    if flavor in ("domestic", "international"):
        gid = fg.get(flavor)
        if gid and gid in NODES:
            note = f"Heuristic: **{flavor.title()}** wording detected → routing toward that pier cluster. Still confirm gate on FIDS / boarding pass."
            return str(gid), note

    gid, band_note = _band_goal(gate_num)
    if gid:
        return gid, band_note
    return None, None


def extract_gate_number_from_text(text: str) -> Optional[int]:
    """First plausible boarding gate number in ``text`` (numeric gates only when no pier letter)."""
    if not text:
        return None
    low = text.lower().strip()

    m = re.search(r"\b(?:gate|boarding(?:\s+gate)?)\s*([a-z])?\s*(\d{1,2})\b", low)
    if m:
        letter, num_s = m.group(1), m.group(2)
        if letter:
            return None
        n = int(num_s)
        if 1 <= n <= 99:
            return n

    m = re.search(r"\bg\s*(\d{1,2})\b", low)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 99:
            return n

    if len(low) <= 4:
        m = re.fullmatch(r"(\d{1,2})", low)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 99:
                return n
    return None


def infer_gate_graph_from_text(text: str) -> Optional[str]:
    """Return a graph node id if ``text`` looks like a gate-only navigation target."""
    n = extract_gate_number_from_text(text)
    if n is None:
        return None
    gid, _ = goal_graph_for_numeric_gate(n, text)
    return gid


def advisory_for_gate_context(user_text: str, resolved_goal_id: str) -> Optional[str]:
    """Append to chat when a numeric gate was interpreted (FIDS / boarding pass reminder)."""
    if not resolved_goal_id or resolved_goal_id not in NODES:
        return None
    n = extract_gate_number_from_text(user_text)
    if n is None:
        return None
    _gid, band_note = goal_graph_for_numeric_gate(n, user_text)
    pol = _policy()
    lines = [
        "**Gate note (T2):** Gates can be swing (domestic/intl varies by day). "
        "Use your **boarding pass** and **FIDS** for the exact gate.",
    ]
    if band_note:
        lines.append(band_note)
    summ = (pol.get("summary") or "").strip()
    if summ:
        lines.append(summ)
    lv = pol.get("levels_hint")
    if lv:
        lines.append(str(lv))
    links = pol.get("official_links") or {}
    if links.get("csmia_home"):
        lines.append(f"Official airport: {links['csmia_home']}")
    return "\n".join(lines)
