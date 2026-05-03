from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, navigation, context

app = FastAPI(title="AI Airport Companion API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers using standardized /api prefix
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(navigation.router, prefix="/api", tags=["Navigation"])
app.include_router(context.router, prefix="/api", tags=["Context"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}
