from fastapi import APIRouter
from app.models.request import ChatRequest
from app.models.response import ChatResponse
from app.services.llm_service import call_llm

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint — calls the local LLM via Ollama
    and returns a structured response.
    """
    reply = call_llm(request.message)

    return ChatResponse(
        type="chat",
        intent="general",
        message=reply,
        data={},
        context={"location": request.location},
    )
