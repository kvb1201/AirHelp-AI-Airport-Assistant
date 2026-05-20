# backend/app/main.py

import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    print("[WARN] HF_TOKEN not found in environment variables")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.api import (
    chat,
    context,
    guided_navigation,
    lost_found,
    map as map_api,
    navigation,
    ocr,
    tts,
    transcribe,
    translate,
)

from app.api import support_tickets, travel_documents

try:
    from app.api import ops
    HAS_OPS = True
except Exception:
    HAS_OPS = False

from app.services import lost_found_service as lost_found_storage
from app.services import operational_state_service as ops_state
from app.services.rag_service import init_rag
from app.services.alert_scheduler import start_alert_scheduler


# ----------------------------
# 🔹 Lifespan (Startup + Shutdown)
# ----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] AI Airport Companion API starting...")

    lost_found_storage.init_db()
    print(
        f"[INFO] Lost & Found storage (SQLite on this laptop): "
        f"{lost_found_storage.get_db_path()}"
    )

    ops_state.load_from_disk()
    print(
        f"[INFO] Operational state (operator bulletins / delays): "
        f"{ops_state.get_data_path()}"
    )

    try:
        init_rag()
        print("[OK] RAG initialized successfully")
    except Exception as e:
        print(f"[ERROR] RAG initialization failed: {e}")

    try:
        start_alert_scheduler()
        print("[INFO] Alert scheduler started")
    except Exception as e:
        print(f"[WARN] Failed to start alert scheduler: {e}")

    yield

    print("[INFO] API shutting down...")


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
app.include_router(
    guided_navigation.router,
    prefix="/api",
    tags=["Guided navigation"]
)

app.include_router(context.router, prefix="/api", tags=["Context"])
app.include_router(map_api.router, prefix="/api", tags=["Map"])
app.include_router(lost_found.router, prefix="/api", tags=["Lost & Found"])
app.include_router(tts.router, prefix="/api", tags=["TTS"])
app.include_router(transcribe.router, prefix="/api", tags=["STT"])
app.include_router(translate.router, prefix="/api", tags=["Translation"])
app.include_router(ocr.router, prefix="/api", tags=["OCR"])
app.include_router(
    support_tickets.router,
    prefix="/api",
    tags=["Support"]
)

if HAS_OPS:
    app.include_router(
        ops.router,
        prefix="/api",
        tags=["Operator ops"]
    )

app.include_router(
    travel_documents.router,
    prefix="/api/travel-documents",
    tags=["Travel Documents"]
)


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
        content={"message": "Internal server error"},
    )