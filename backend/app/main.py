# backend/app/main.py
"""
Juggler v2 - FastAPI application with authentication
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import time
import traceback
from sqlalchemy.orm import Session

# Import database and models
from app.database import engine, get_db
from app.models.user import Base, User
from app.models.config import SystemConfig
from app.routers import auth as auth_router
from app.routers import config as config_router

# Create database tables
Base.metadata.create_all(bind=engine)

# Temporary in-memory storage for conversations (until we add database)
conversations = {}

app = FastAPI(
    title="Juggler v2",
    description="Multi-model AI chat system",
    version="2.0.0-alpha"
)

# CORS configuration for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models as defined in the contract
class ChatRequest(BaseModel):
    message: str
    provider: str = "ollama"  # Default to ollama for Phase 1
    model: str = "llama3:8b"  # Default model
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    provider: str
    model: str
    tokens: dict = {"input": 0, "output": 0}  # Placeholder
    latency_ms: int

# Include routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(config_router.router, prefix="/api")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Juggler v2",
        "phase": "1 - Core Chat"
    }

@app.post("/api/chat/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Main chat endpoint - Phase 1 implementation with real Ollama
    """
    start_time = time.time()
    
    # Generate or use existing conversation ID
    conversation_id = request.conversation_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    
    # Store conversation (temporary in-memory)
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    
    # Add user message to conversation history
    conversations[conversation_id].append({
        "role": "user",
        "content": request.message,
        "message_id": message_id
    })
    
    try:
        # Import here to avoid circular imports
        from app.services.provider_service import get_provider_service
        provider_service = get_provider_service()
        
        # Send to Ollama via provider service
        response = await provider_service.send_message(
            provider_name=request.provider,
            model=request.model,
            messages=[{"role": "user", "content": request.message}],
            temperature=0.7
        )
        
        response_text = response.content
        tokens = response.tokens_used
        
    except Exception as e:
        # Detailed error logging
        print(f"Provider error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Fallback to echo mode if Ollama is not available
        response_text = f"[Ollama Error - Echo Mode] {request.message}"
        tokens = {"input": 0, "output": 0}
    
    # Store assistant response
    assistant_message_id = str(uuid.uuid4())
    conversations[conversation_id].append({
        "role": "assistant", 
        "content": response_text,
        "message_id": assistant_message_id
    })
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    return ChatResponse(
        response=response_text,
        conversation_id=conversation_id,
        message_id=assistant_message_id,
        provider=request.provider,
        model=request.model,
        tokens=tokens,
        latency_ms=latency_ms
    )

@app.get("/api/chat/conversations")
async def get_conversations():
    """Get list of conversations (Phase 1: from memory)"""
    return {
        "conversations": [
            {
                "id": conv_id,
                "title": f"Conversation {idx + 1}",
                "created_at": "2024-01-01T00:00:00",  # Placeholder
                "updated_at": "2024-01-01T00:00:00",  # Placeholder
                "message_count": len(messages)
            }
            for idx, (conv_id, messages) in enumerate(conversations.items())
        ]
    }

@app.get("/api/providers")
async def get_providers():
    """
    Get available providers and their models
    Phase 1: Real Ollama check
    """
    # Import here to avoid circular imports
    from app.services.provider_service import get_provider_service
    provider_service = get_provider_service()
    
    return {
        "providers": await provider_service.get_available_providers()
    }

@app.get("/api/test-ollama")
async def test_ollama():
    """Test endpoint to debug Ollama connection"""
    import httpx
    
    try:
        # Test direct connection to Ollama
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            response.raise_for_status()
            return {
                "ollama_direct": "OK",
                "models": response.json()
            }
    except Exception as e:
        return {
            "ollama_direct": "FAILED",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)