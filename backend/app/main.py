# backend/app/main.py
"""
Juggler v2 - FastAPI application with authentication
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uuid
import time
import traceback
from sqlalchemy.orm import Session
from datetime import datetime

# Import database and models
from app.database import engine, get_db
from app.models.user import Base, User
from app.models.system_config import SystemConfig
from app.models.chat import Conversation, Message
from app.routers import auth as auth_router
from app.routers import config as config_router
from app.services.auth_service import auth_service

# Create database tables
Base.metadata.create_all(bind=engine)

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
    provider: str = "ollama"
    model: str = "llama3:8b"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    provider: str
    model: str
    tokens: dict = {"input": 0, "output": 0}
    latency_ms: int

# Include routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(config_router.router, prefix="/api/config", tags=["config"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Juggler v2",
        "phase": "2 - DB Persistence"
    }

# DEPENDENCY: Get current user from token
async def get_current_user_from_token(
    db: Session = Depends(get_db), 
    token: str = Depends(auth_router.oauth2_scheme)
) -> User:
    """Get current user from JWT token"""
    token_data = auth_service.decode_token(token)
    
    if not token_data or not token_data.user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@app.post("/api/chat/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Main chat endpoint - Phase 2: With database persistence
    """
    start_time = time.time()
    
    # Get or create conversation
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=current_user.id,
            title=request.message[:50]
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Save user message to database
    user_message = Message(
        conversation_id=str(conversation.id),
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    try:
        # Import here to avoid circular imports
        from app.services.provider_service import get_provider_service
        provider_service = get_provider_service()
        
        # Load all messages from this conversation for context
        all_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.timestamp).all()
        
        # Convert to provider format
        context_messages = [
            {"role": msg.role, "content": msg.content} 
            for msg in all_messages
        ]
        
        # Send to provider with full context
        response = await provider_service.send_message(
            provider_name=request.provider,
            model=request.model,
            messages=context_messages,
            temperature=0.7
        )
        
        response_text = response.content
        tokens = response.tokens_used
        
    except Exception as e:
        # Detailed error logging
        print(f"Provider error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Fallback to echo mode if provider fails
        response_text = f"[Provider Error - Echo Mode] {request.message}"
        tokens = {"input": 0, "output": 0}
    
    # Save assistant response to database
    assistant_message = Message(
        conversation_id=str(conversation.id),
        role="assistant",
        content=response_text,
        provider=request.provider,
        model=request.model,
        tokens_input=tokens.get("input", 0),
        tokens_output=tokens.get("output", 0)
    )
    db.add(assistant_message)
    
    # Update conversation
    setattr(conversation, "updated_at", datetime.utcnow())
    setattr(conversation, "total_tokens", (getattr(conversation, "total_tokens", 0) or 0) + tokens.get("input", 0) + tokens.get("output", 0))
    
    db.commit()
    db.refresh(assistant_message)
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    return ChatResponse(
        response=response_text,
        conversation_id=str(conversation.id),
        message_id=str(assistant_message.id),
        provider=request.provider,
        model=request.model,
        tokens=tokens,
        latency_ms=latency_ms
    )

@app.get("/api/chat/conversations")
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get list of conversations for current user"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    
    return {
        "conversations": [
            {
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "message_count": len(conv.messages),
                "total_tokens": conv.total_tokens
            }
            for conv in conversations
        ]
    }

@app.get("/api/chat/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get all messages for a conversation"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp).all()
    
    return {
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "provider": msg.provider,
                "model": msg.model,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]
    }

@app.get("/api/providers")
async def get_providers():
    """Get available providers and their models"""
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