from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    user_id: str = "user_123"
    message: str
    location: str = "entrance"
    language: str = "en"
    context_id: Optional[str] = None
