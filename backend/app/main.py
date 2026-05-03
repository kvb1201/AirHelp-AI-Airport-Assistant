# backend/app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import chat, context, navigation
from app.services.rag_service import build_knowledge_base

app = FastAPI(title="AI Airport Companion API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(navigation.router, prefix="/api", tags=["Navigation"])
app.include_router(context.router, prefix="/api", tags=["Context"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


@app.on_event("startup")
async def startup_event():
    # Build normalized place and RAG files at startup so the backend can answer
    # structured airport questions from the raw dataset without manual steps.
    build_knowledge_base()
    print("AI Airport Companion API started")

