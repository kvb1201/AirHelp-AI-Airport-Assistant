# backend/app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.api import chat, context, guided_navigation, map as map_api, navigation, tts
from app.services.rag_service import init_rag


# ----------------------------
# 🔹 Lifespan (Startup + Shutdown)
# ----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 AI Airport Companion API starting...")

    try:
        init_rag()
        print("✅ RAG initialized successfully")
    except Exception as e:
        print(f"❌ RAG initialization failed: {e}")

    yield

    print("🛑 API shutting down...")


# ----------------------------
# 🔹 App Init
# ----------------------------
app = FastAPI(
    title="AI Airport Companion API",
    lifespan=lifespan
)


# ----------------------------
# 🔹 CORS (for frontend)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK for hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# 🔹 Routers
# ----------------------------
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(navigation.router, prefix="/api", tags=["Navigation"])
app.include_router(guided_navigation.router, prefix="/api", tags=["Guided navigation"])
app.include_router(context.router, prefix="/api", tags=["Context"])
app.include_router(map_api.router, prefix="/api", tags=["Map"])
app.include_router(tts.router, prefix="/api", tags=["TTS"])


# ----------------------------
# 🔹 Health Check
# ----------------------------
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ----------------------------
# 🔹 Global Error Handler
# ----------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "details": str(exc),  # 🔥 helpful during dev (remove in prod)
        },
    )