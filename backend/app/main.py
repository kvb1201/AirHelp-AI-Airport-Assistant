# backend/app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import chat, context, guided_navigation, map as map_api, navigation
from app.services.rag_service import init_rag

app = FastAPI(title="AI Airport Companion API")


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


# ----------------------------
# 🔹 Startup Event
# ----------------------------
@app.on_event("startup")
async def startup_event():
    print("🚀 AI Airport Companion API started")

    try:
        init_rag()   # 🔥 Initialize RAG once
        print("✅ RAG initialized successfully")
    except Exception as e:
        print(f"❌ RAG initialization failed: {e}")