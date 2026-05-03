"""Process-local in-memory user context (hackathon / demo)."""

from typing import Any

_store: dict[str, dict[str, Any]] = {}


class StateManager:
    @staticmethod
    def get(user_id: str) -> dict[str, Any]:
        return dict(_store.get(user_id, {}))

    @staticmethod
    def merge(user_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        cur = dict(_store.get(user_id, {}))
        for k, v in patch.items():
            if v is None:
                cur.pop(k, None)
            else:
                cur[k] = v
        _store[user_id] = cur
        return dict(cur)

    @staticmethod
    def clear(user_id: str) -> None:
        _store.pop(user_id, None)
