# backend/app/routers/chat.py

"""
Chat router - handles chat functionality with encrypted API key support
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, Field, validator
import bleach

from app.models.auth_utils import get_current_user, TokenData
from app.services.provider_service import get_user_provider_service
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
    """Send a message to AI provider using user's encrypted API keys"""
    try:
        # Ensure user_id is not None
        if not current_user.user_id:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
        
        # Handle model None case early in the function
        model_value = message.model if message.model is not None else "default"
        
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
            model=model_value
        )
        
        # Get user-specific provider service
        provider_service = await get_user_provider_service(current_user.user_id)
        
        # Get the specific provider instance for this user
        try:
            provider_instance = await provider_service.get_provider_for_user(
                message.provider, 
                current_user.user_id
            )
        except ValueError as e:
            # Provider not available for this user
            error_response = f"Provider '{message.provider}' not available. Please configure your API key for this provider."
            
            # Store error message
            add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=error_response,
                provider=message.provider,
                model=model_value
            )
            
            return {
                "response": error_response,
                "conversation_id": conversation_id,
                "provider": message.provider,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        
        # Create context package for the provider
        messages = []  # In a full implementation, you'd get conversation history here
        
        context_package = provider_instance.create_context_package(
            messages=messages,
            target_model=model_value,
            user_query=message.content
        )
        
        # Send message to AI provider
        try:
            ai_response = await provider_instance.send_message(
                context_package=context_package,
                model_id=model_value,
                temperature=0.7,
                max_tokens=2048
            )
            
            # Extract response content
            response_content = ai_response.message.content
            
            # Store assistant response
            add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response_content,
                provider=message.provider,
                model=model_value
            )
            
            return {
                "response": response_content,
                "conversation_id": conversation_id,
                "provider": message.provider,
                "model": model_value,
                "timestamp": datetime.utcnow().isoformat(),
                "tokens": {
                    "input": ai_response.input_tokens,
                    "output": ai_response.output_tokens
                },
                "latency_ms": ai_response.latency_ms
            }
            
        except Exception as provider_error:
            # Handle provider-specific errors
            error_message = f"Error from {message.provider}: {str(provider_error)}"
            
            # Store error message
            add_message(
                conversation_id=conversation_id,
                role="assistant", 
                content=error_message,
                provider=message.provider,
                model=model_value
            )
            
            return {
                "response": error_message,
                "conversation_id": conversation_id,
                "provider": message.provider,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(provider_error)
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

@router.get("/providers")
async def get_available_providers(
    current_user: TokenData = Depends(get_current_user)
):
    """Get available providers for the current user"""
    if not current_user.user_id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")
    
    try:
        provider_service = await get_user_provider_service(current_user.user_id)
        providers = await provider_service.get_all_providers(current_user.user_id)
        
        return {
            "providers": providers,
            "user_id": current_user.user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {str(e)}")

@router.post("/providers/{provider_name}/refresh")
async def refresh_provider(
    provider_name: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Refresh models for a specific provider"""
    if not current_user.user_id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")
    
    try:
        provider_service = await get_user_provider_service(current_user.user_id)
        status = await provider_service.refresh_provider(provider_name, current_user.user_id)
        
        return {
            "provider": provider_name,
            "status": status,
            "user_id": current_user.user_id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh provider: {str(e)}")

# New endpoint for managing user API keys
@router.post("/api-keys/{provider}")
async def store_user_api_key(
    provider: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Store an encrypted API key for a provider"""
    if not current_user.user_id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")
    
    try:
        body = await request.json()
        api_key = body.get("api_key")
        key_name = body.get("key_name", f"{provider.title()} API Key")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required")
        
        # Store the encrypted API key
        from app.models.security_models import store_encrypted_api_key
        from app.database import get_db_context
        
        with get_db_context() as db:
            encrypted_key = store_encrypted_api_key(
                user_id=current_user.user_id,
                provider=provider,
                api_key=api_key,
                key_name=key_name
            )
            db.add(encrypted_key)
            db.commit()
        
        return {
            "message": f"API key for {provider} stored successfully",
            "provider": provider,
            "key_name": key_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store API key: {str(e)}")

@router.get("/api-keys")
async def list_user_api_keys(
    current_user: TokenData = Depends(get_current_user)
):
    """List user's stored API keys (without revealing the keys)"""
    if not current_user.user_id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")
    
    try:
        from app.models.security_models import list_user_api_keys
        api_keys = list_user_api_keys(current_user.user_id)
        
        return {
            "api_keys": api_keys,
            "user_id": current_user.user_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list API keys: {str(e)}")

@router.delete("/api-keys/{provider}")
async def delete_user_api_key(
    provider: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Delete a user's API key for a provider"""
    if not current_user.user_id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")
    
    try:
        from app.models.security_models import delete_api_key
        deleted = delete_api_key(current_user.user_id, provider)
        
        if deleted:
            return {
                "message": f"API key for {provider} deleted successfully",
                "provider": provider
            }
        else:
            raise HTTPException(status_code=404, detail=f"No API key found for provider {provider}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete API key: {str(e)}")