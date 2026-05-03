from pydantic import BaseModel
from typing import Any, Dict, Optional


class ChatResponse(BaseModel):
    type: str = "chat"
    intent: Optional[str] = None
    message: str
    data: Dict[str, Any] = {}
    context: Dict[str, Any] = {}