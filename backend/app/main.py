# backend/app/main.py

"""
Juggler API - Clean and minimal main.py
Routes and app configuration only
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.middleware import setup_middleware
from app.routers import auth, chat, providers, admin
from app.services.provider_service import provider_service
from app.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Juggler API...")
    
    # Initialize database
    init_db()
    
    # Initialize provider service
    await provider_service.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Juggler API...")

# Create FastAPI app
app = FastAPI(
    title="Juggler API",
    description="Self-hosted multi-model AI chat with dynamic model loading",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Setup middleware
setup_middleware(app)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(providers.router, prefix="/api/providers", tags=["Providers"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Juggler API",
        "version": "2.1.0",
        "status": "running",
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)