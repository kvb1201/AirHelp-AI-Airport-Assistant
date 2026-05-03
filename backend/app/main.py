# backend/app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import chat, navigation, context

app = FastAPI(title="AI Airport Companion API")


# ----------------------------
# 🔹 CORS (for frontend)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ok for hackathon demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# 🔹 Routers
# ----------------------------
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(navigation.router, prefix="/api", tags=["Navigation"])
app.include_router(context.router, prefix="/api", tags=["Context"])


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
# 🔹 Startup Event (optional but useful)
# ----------------------------
@app.on_event("startup")
async def startup_event():
    print("🚀 AI Airport Companion API started")