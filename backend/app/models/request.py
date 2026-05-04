from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    user_id: str = "user_123"
    message: str
    location: Optional[str] = None
    """Semantic start zone; omit to keep last known (e.g. entrance → entrance_main)."""
    destination: Optional[str] = None
    """Optional explicit goal (e.g. gate_b12); else parsed from message."""
    flight_number: Optional[str] = None
    boarding_time: Optional[str] = None
    departure_time: Optional[str] = None
    language: str = "en"
    context_id: Optional[str] = None
