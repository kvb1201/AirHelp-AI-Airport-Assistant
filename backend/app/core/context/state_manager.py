"""Persistent file-based user context storage (offline JSON)."""

import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = Path(__file__).resolve().parents[3]
USERS_STORAGE_PATH = Path(__file__).resolve().parents[2] / "data" / "users.json"
IST = timezone(timedelta(hours=5, minutes=30))


def _ensure_users_file() -> None:
    """Create users.json if it doesn't exist."""
    if not USERS_STORAGE_PATH.exists():
        USERS_STORAGE_PATH.write_text(json.dumps({}, indent=2), encoding="utf-8")


def _load_users_db() -> dict[str, dict[str, Any]]:
    """Load all users from JSON file."""
    try:
        content = USERS_STORAGE_PATH.read_text(encoding="utf-8")
        return json.loads(content) if content.strip() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_users_db(data: dict[str, dict[str, Any]]) -> None:
    """Save all users to JSON file."""
    _ensure_users_file()
    USERS_STORAGE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


class StateManager:
    @staticmethod
    def get(user_id: str) -> dict[str, Any]:
        """Fetch user context from persistent storage."""
        _ensure_users_file()
        db = _load_users_db()
        return dict(db.get(user_id, {}))

    @staticmethod
    def merge(user_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        """Merge patch into user context and persist to disk."""
        _ensure_users_file()
        db = _load_users_db()
        
        # Get current user context
        cur = dict(db.get(user_id, {}))
        
        # Apply patch
        for k, v in patch.items():
            if v is None:
                cur.pop(k, None)
            else:
                cur[k] = v
        
        # Add metadata
        now_ist = datetime.now(IST).isoformat()
        if "user_id" not in cur:
            cur["user_id"] = user_id
            cur["created_at"] = now_ist
        cur["updated_at"] = now_ist
        
        # Save back to disk
        db[user_id] = cur
        _save_users_db(db)
        
        return dict(cur)

    @staticmethod
    def clear(user_id: str) -> None:
        """Remove user from persistent storage."""
        _ensure_users_file()
        db = _load_users_db()
        db.pop(user_id, None)
        _save_users_db(db)

    @staticmethod
    def list_all_users() -> dict[str, dict[str, Any]]:
        """Get all users (useful for debugging and alerts)."""
        _ensure_users_file()
        return _load_users_db()
