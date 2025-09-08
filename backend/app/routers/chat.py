# backend/app/routers/chat.py

"""
Chat router - handles chat functionality
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, Field, validator
import bleach

from app.models.auth_utils import get_current_user, TokenData
from app.services.chat_service import chat_service
from app.database import (
    create_conversation, add_message, 
    get_conversation_messages, get_user_conversations
)
from app.config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class MessageRequest(BaseModel):
    """Chat message request"""
    content: str = Field(..., min_length=1, max_length=10000)
    provider: str = Field(..., pattern="^(ollama|groq|gemini)$")
    conversation_id: str | None = None
    model: str | None = None
    
    @validator('content')
    def sanitize_content(cls, v):
        """Sanitize message content"""
        return bleach.clean(v, tags=['p', 'br', 'strong', 'em', 'code', 'pre'], strip=True)

@router.post("/send")
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}seconds")
async def send_message(
    request: Request,
    message: MessageRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Send a message to AI provider"""
    try:
        # Ensure user_id is not None
        if not current_user.user_id:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
        
        # Create or get conversation
        if not message.conversation_id:
            conv = create_conversation(
                user_id=current_user.user_id,  # Now guaranteed to be not None
                title=message.content[:50]
            )
            # Ensure we get the string value, not the column object
            conversation_id = str(conv.id) if conv.id is not None else ""
            if not conversation_id:
                raise HTTPException(status_code=500, detail="Failed to create conversation")
        else:
            conversation_id = message.conversation_id
        
        # Store user message
        add_message(
            conversation_id=conversation_id,
            role="user",
            content=message.content,
            provider=message.provider,
            model=message.model
        )
        
        # Get AI response
        response = await chat_service.get_response(
            provider=message.provider,
            model=message.model,
            prompt=message.content
        )

        # Store assistant response
        add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
            provider=message.provider,
            model=model_value  # Use the same model_value we defined above
        )
        
        return {
            "response": response,
            "conversation_id": conversation_id,
            "provider": message.provider,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations")
async def get_conversations(
    current_user: TokenData = Depends(get_current_user)
):
    """Get user's conversations"""
    # Ensure user_id is not None
    if not current_user.user_id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")
        
    conversations = get_user_conversations(current_user.user_id)
    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat()
            } for c in conversations
        ],
        "total": len(conversations)
    }

@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get specific conversation"""
    messages = get_conversation_messages(conversation_id)
    return {
        "id": conversation_id,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "provider": m.provider,
                "model": m.model,
                "created_at": m.created_at.isoformat()
            } for m in messages
        ],
        "created_at": datetime.utcnow().isoformat()
    }