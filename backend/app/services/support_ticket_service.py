"""Create support / issue tickets and append them to a local JSONL log (demo / hackathon)."""

from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TICKETS_FILE = DATA_DIR / "support_tickets.jsonl"

ISSUE_CATEGORIES: dict[str, str] = {
    "wrong_information": "Wrong or outdated information",
    "app_issue": "Problem with AirHelp (this app)",
    "directions_or_map": "Directions or map did not match the terminal",
    "accessibility": "Accessibility or special assistance",
    "safety_security": "Safety or security",
    "other": "Something else",
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    if len(s) > 320 or not _EMAIL_RE.match(s):
        raise ValueError("Invalid email address.")
    return s


def create_ticket(
    *,
    category: str,
    description: str,
    where_hint: str | None = None,
    email: str | None = None,
    location_graph_id: str | None = None,
) -> dict:
    cat = (category or "").strip()
    if cat not in ISSUE_CATEGORIES:
        allowed = ", ".join(sorted(ISSUE_CATEGORIES))
        raise ValueError(f"Unknown category. Use one of: {allowed}")

    desc = (description or "").strip()
    if len(desc) < 10:
        raise ValueError("Description must be at least 10 characters.")
    if len(desc) > 4000:
        raise ValueError("Description is too long (max 4000 characters).")

    where = (where_hint or "").strip() or None
    if where and len(where) > 500:
        raise ValueError("Location hint is too long (max 500 characters).")

    loc = (location_graph_id or "").strip() or None
    if loc and len(loc) > 120:
        raise ValueError("Location id is too long.")

    email_norm = _validate_email(email)

    now = datetime.now(timezone.utc)
    ticket_id = f"AH-T2-{now.strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"

    record = {
        "ticket_id": ticket_id,
        "created_at": now.isoformat(),
        "category": cat,
        "category_label": ISSUE_CATEGORIES[cat],
        "description": desc,
        "where_hint": where,
        "email": email_norm,
        "location_graph_id": loc,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with TICKETS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = desc.replace("\n", " ").strip()
    if len(summary) > 160:
        summary = summary[:157] + "…"

    return {
        "ticket_id": ticket_id,
        "created_at": record["created_at"],
        "category": cat,
        "category_label": ISSUE_CATEGORIES[cat],
        "summary": summary,
    }


def list_categories() -> list[dict[str, str]]:
    return [{"id": k, "label": v} for k, v in ISSUE_CATEGORIES.items()]
