from app.core.context.state_manager import StateManager

def get_user_context(user_id: str):
    """
    Retrieves the current context for a user (flight info, location, past interaction state).
    """
    pass

def update_user_context(user_id: str, new_state: dict):
    """
    Updates the existing context for a user.
    """
    pass

def reset_user_context(user_id: str):
    """
    Clears or resets the context for a user.
    """
    pass
