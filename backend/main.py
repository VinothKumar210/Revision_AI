"""
Revision AI — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import get_settings
from services.database import connect_db, disconnect_db
from services.scheduler_service import start_scheduler, stop_scheduler
from routes.chat import router as chat_router
from routes.enhance import router as enhance_router
from routes.revise import router as revise_router
from routes.webhook import router as webhook_router
from routes.topics import router as topics_router
from routes.schedules import router as schedules_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    settings = get_settings()
    logger.info("🚀 Revision AI Backend starting...")
    logger.info(f"📡 Frontend URL: {settings.frontend_url}")
    logger.info(f"🧠 LLM Model: {settings.groq_model}")

    # Connect to MongoDB
    await connect_db()

    # Start scheduler (only if DB connected)
    await start_scheduler()

    yield

    # Stop scheduler
    await stop_scheduler()
    # Disconnect from MongoDB
    await disconnect_db()
    logger.info("🛑 Revision AI Backend shutting down...")


app = FastAPI(
    title="Revision AI",
    description="Agentic AI-powered study revision backend",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend origin
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with welcome message."""
    return {
        "message": "Welcome to Revision AI API",
        "docs": "/docs",
        "health": "/health",
    }


# Include route modules
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(enhance_router, prefix="/enhance", tags=["Enhance"])
app.include_router(revise_router, prefix="/revise", tags=["Revise"])
app.include_router(webhook_router, prefix="/webhook", tags=["Webhook"])
app.include_router(topics_router, prefix="/topics", tags=["Topics"])
app.include_router(schedules_router, prefix="/schedules", tags=["Schedules"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "revision-ai-backend",
        "version": "0.1.0",
    }
