from app.core.context.state_manager import StateManager


def get_user_context(user_id: str) -> dict | None:
    ctx = StateManager.get(user_id)
    return ctx if ctx else None


def update_user_context(user_id: str, new_state: dict) -> None:
    StateManager.merge(user_id, new_state)


def reset_user_context(user_id: str) -> None:
    StateManager.clear(user_id)
