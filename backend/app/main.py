# backend/app/main.py
"""
Main FastAPI application for Juggler v3 with Context Engine
Includes Phase C endpoints for context transparency, variant management, and provider health
"""

from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, engine, Base
from app.models.user import User
from app.models.chat import Conversation, Message
from app.models.message_variants import MessageVariant
from app.models.context_engine import ContextSnapshot, ProviderHealth
from app.models.schemas import (
    UserCreate, UserLogin, Token, 
    ChatRequest, ChatResponse, ConversationResponse,
    MessageResponse, MessageVariantResponse, MessageVariantRequest,
    MessageVariantSelectRequest, ContextSnapshotResponse, ContextMessageInfo,
    ProviderHealthResponse, ProvidersHealthResponse
)
from app.services.auth_service import auth_service, get_current_user
from app.services.provider_service import get_provider_service
from app.services.context_orchestrator import context_orchestrator
from app.settings import settings
from app.providers.base import ContextPackage
from app.routers import auth as auth_router
from app.routers import config as config_router

# Create FastAPI app
app = FastAPI(
    title="Juggler AI Chat System",
    version="3.0.0",
    description="Multi-model AI chat with Context Engine"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(config_router.router, prefix="/api/config", tags=["config"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Initialize Context Orchestrator
    if settings.ENABLE_CONTEXT_ENGINE and settings.is_postgres():
        await context_orchestrator.initialize()
        print("[OK] Context Orchestrator initialized")
    else:
        print("[INFO] Context Orchestrator disabled (requires PostgreSQL)")

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "name": "Juggler AI Chat System",
        "version": "3.0.0",
        "status": "running",
        "context_engine": settings.ENABLE_CONTEXT_ENGINE and settings.is_postgres()
    }

@app.post("/api/chat/send")
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to the AI provider using Context Orchestrator if enabled"""
    
    # Check if Context Engine is enabled
    if settings.ENABLE_CONTEXT_ENGINE and settings.is_postgres():
        # Use Context Orchestrator for intelligent context management
        try:
            result = await context_orchestrator.process_message(
                db=db,
                user_id=current_user.id,
                conversation_id=request.conversation_id,
                message=request.message,
                provider=request.provider,
                model=request.model
            )
            
            # Get any variants for this message
            variants = db.query(MessageVariant).filter(
                MessageVariant.original_message_id == result.message_id
            ).all()
            
            return ChatResponse(
                response=result.response,
                conversation_id=result.conversation_id,
                message_id=result.message_id,
                provider=result.provider_used,
                model=result.model_used,
                tokens=result.tokens,
                latency_ms=result.latency_ms,
                variants=[MessageVariantResponse.from_orm(v) for v in variants]
            )
        except Exception as e:
            print(f"Context Orchestrator error: {e}")
            print("Falling back to direct provider call")
            db.rollback()
    
    # Original implementation (fallback or if Context Engine disabled)
    provider_service = get_provider_service()
    
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
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Get conversation history for context
    previous_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.timestamp).all()
    
    # Build context with previous messages
    context_messages = []
    for msg in previous_messages:
        context_messages.append({
            "role": msg.role,
            "content": msg.content
        })
    context_messages.append({
        "role": "user",
        "content": request.message
    })
    
    # Create context package
    context = ContextPackage(messages=context_messages)
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
        timestamp=datetime.utcnow()
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    try:
        # Send to provider
        provider_response = await provider_service.send_message(
            request.provider,
            context,
            request.model
        )
        
        # Save assistant response
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=provider_response.response,
            provider=provider_response.provider,
            model=provider_response.model,
            tokens_input=provider_response.tokens_used.get('input', 0),
            tokens_output=provider_response.tokens_used.get('output', 0),
            timestamp=datetime.utcnow()
        )
        db.add(assistant_message)
        
        # Update conversation
        conversation.updated_at = datetime.utcnow()
        if provider_response.tokens_used:
            total_tokens = provider_response.tokens_used.get('input', 0) + provider_response.tokens_used.get('output', 0)
            conversation.total_tokens = (conversation.total_tokens or 0) + total_tokens
        
        db.commit()
        db.refresh(assistant_message)
        
        return ChatResponse(
            response=provider_response.response,
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            provider=provider_response.provider,
            model=provider_response.model,
            tokens=provider_response.tokens_used,
            variants=[]
        )
        
    except Exception as e:
        db.rollback()
        db.add(user_message)
        db.commit()
        
        error_message = f"Error: {str(e)}"
        
        error_response = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=error_message,
            provider=request.provider,
            model=request.model,
            timestamp=datetime.utcnow()
        )
        db.add(error_response)
        db.commit()
        
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/rerun")
async def rerun_message(
    request: MessageVariantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rerun a message with a different provider/model to generate a variant
    Preserves the original context from the message's context snapshot
    """
    try:
        # Get the original message
        original_message = db.query(Message).filter(
            Message.id == request.original_message_id
        ).first()
        
        if not original_message:
            print(f"DEBUG: Message not found: {request.original_message_id}")
            raise HTTPException(status_code=404, detail="Message not found")
        
        print(f"DEBUG: Found message {request.original_message_id} in conversation {original_message.conversation_id}")
        
        # Verify user owns the conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == original_message.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        print(f"DEBUG: Current user: {current_user.id}, Conversation user: {original_message.conversation_id if not conversation else 'found'}")
        
        if not conversation:
            print(f"DEBUG: User {current_user.id} does not own conversation {original_message.conversation_id}")
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Get the context snapshot for this message
        context_snapshot = db.query(ContextSnapshot).filter(
            ContextSnapshot.generating_message_id == request.original_message_id
        ).first()
        
        if not context_snapshot:
            print(f"DEBUG: No context snapshot found for message {request.original_message_id}")
            raise HTTPException(status_code=404, detail="Context snapshot not found - message may be from before Phase C was enabled")
        
        # Extract the context package from snapshot
        import json
        snapshot_data = context_snapshot.snapshot_data
        if isinstance(snapshot_data, str):
            snapshot_data = json.loads(snapshot_data)
        
        # Get messages from snapshot - handle both string and list
        messages = snapshot_data.get("messages", [])
        if isinstance(messages, str):
            messages = json.loads(messages)
        
        context = ContextPackage(
            messages=messages,
            temperature=snapshot_data.get("temperature", 0.7),
            max_tokens=snapshot_data.get("max_tokens", 4000)
        )
        
        # Call the new provider with preserved context
        provider_service = get_provider_service()
        
        try:
            provider_response = await provider_service.send_message(
                provider_name=request.provider,
                model=request.model,
                messages=context.messages,
                system_prompt=context.system_prompt
            )
            
            # Create a variant (not canonical yet)
            variant = MessageVariant.create(
                db=db,
                original_message_id=request.original_message_id,
                content=provider_response.content,
                provider=request.provider,
                model=request.model,
                tokens_input=provider_response.tokens_used.get('input', 0),
                tokens_output=provider_response.tokens_used.get('output', 0),
                context_hash=context_snapshot.context_hash,
                is_canonical=False
            )
            
            # Update conversation token count
            total_tokens = provider_response.tokens_used.get('input', 0) + provider_response.tokens_used.get('output', 0)
            conversation.total_tokens += total_tokens
            db.commit()
            
            # Get all variants for this message
            all_variants = db.query(MessageVariant).filter(
                MessageVariant.original_message_id == request.original_message_id
            ).all()
            
            return {
                "variant": MessageVariantResponse.from_orm(variant),
                "all_variants": [MessageVariantResponse.from_orm(v) for v in all_variants]
            }
            
        except Exception as e:
            print(f"DEBUG: Provider error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Provider error: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Rerun endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/api/chat/variants/select")
async def select_variant(
    request: MessageVariantSelectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Select a variant as an alternative answer
    Creates a NEW message with the variant's content instead of updating the original
    Both original and alternative remain in the conversation
    Original message is marked as inactive for display purposes
    """
    try:
        # Get the variant
        variant = db.query(MessageVariant).filter(
            MessageVariant.id == request.variant_id
        ).first()
        
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        # Get the original message
        original_message = db.query(Message).filter(
            Message.id == request.original_message_id
        ).first()
        
        if not original_message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Verify user owns the conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == original_message.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Create a NEW message with the variant's content
        # (don't update the original)
        new_message = Message(
            conversation_id=original_message.conversation_id,
            role="assistant",
            content=variant.content,
            provider=variant.provider,
            model=variant.model,
            tokens_input=variant.tokens_input,
            tokens_output=variant.tokens_output,
            timestamp=datetime.utcnow()
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # Mark variant as canonical for tracking
        variant.is_canonical = True
        
        # Update conversation tokens
        total_tokens = variant.tokens_input + variant.tokens_output
        conversation.total_tokens += total_tokens
        db.commit()
        
        return {
            "new_message": MessageResponse(
                id=new_message.id,
                role=new_message.role,
                content=new_message.content,
                provider=new_message.provider,
                model=new_message.model,
                timestamp=new_message.timestamp.isoformat() if new_message.timestamp else None
            ),
            "deactivated_message_id": request.original_message_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Select variant error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/api/chat/messages/{message_id}/context")
async def get_message_context(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the context used for generating a specific message
    Returns raw context package and metadata
    """
    # Get the message
    message = db.query(Message).filter(
        Message.id == message_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Verify user owns the conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == message.conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Get context snapshot
    snapshot = db.query(ContextSnapshot).filter(
        ContextSnapshot.generating_message_id == message_id
    ).first()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Context not found for this message")
    
    # Parse snapshot data
    import json
    snapshot_data = snapshot.snapshot_data
    if isinstance(snapshot_data, str):
        snapshot_data = json.loads(snapshot_data)
    
    # Parse metadata
    snapshot_metadata = snapshot.snapshot_metadata
    if isinstance(snapshot_metadata, str):
        snapshot_metadata = json.loads(snapshot_metadata)
    
    # Convert to readable format
    messages = []
    for msg in snapshot_data.get("messages", []):
        messages.append(ContextMessageInfo(
            role=msg.get("role", ""),
            content=msg.get("content", ""),
            metadata=msg.get("metadata")
        ))
    
    return ContextSnapshotResponse(
        context_hash=snapshot.context_hash,
        messages=messages,
        temperature=snapshot_data.get("temperature", 0.7),
        max_tokens=snapshot_data.get("max_tokens", 4000),
        metadata=snapshot_metadata
    )

@app.get("/api/providers/health")
async def get_providers_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get health status of all providers with token usage statistics
    Includes failure counts, circuit breaker status, and token metrics
    """
    # Get all provider health records
    provider_health_records = db.query(ProviderHealth).all()
    
    providers_health = {}
    for health in provider_health_records:
        # Calculate total tokens for this provider
        total_input = db.query(Message).filter(
            Message.provider == health.provider
        ).with_entities(Message.tokens_input).all()
        
        total_output = db.query(Message).filter(
            Message.provider == health.provider
        ).with_entities(Message.tokens_output).all()
        
        tokens_input_total = sum(t[0] for t in total_input if t[0])
        tokens_output_total = sum(t[0] for t in total_output if t[0])
        
        providers_health[health.provider] = ProviderHealthResponse(
            provider=health.provider,
            status=health.status,
            failure_count=health.failure_count,
            last_failure_at=health.last_failure_at.isoformat() if health.last_failure_at else None,
            opened_until=health.opened_until.isoformat() if health.opened_until else None,
            tokens_input_total=tokens_input_total,
            tokens_output_total=tokens_output_total,
            updated_at=health.updated_at.isoformat() if health.updated_at else None
        )
    
    return ProvidersHealthResponse(providers=providers_health)

@app.get("/api/chat/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get user's conversations"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).limit(limit).all()
    
    return {
        "conversations": [
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at.isoformat() if conv.created_at else None,
                updated_at=conv.updated_at.isoformat() if conv.updated_at else None,
                message_count=len(conv.messages)
            ) for conv in conversations
        ]
    }

@app.get("/api/chat/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages for a conversation"""
    # Verify conversation belongs to user
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
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                provider=msg.provider,
                model=msg.model,
                timestamp=msg.timestamp.isoformat() if msg.timestamp else None
            ) for msg in messages
        ]
    }

@app.get("/api/providers")
async def get_providers():
    """Get available providers and their models"""
    provider_service = get_provider_service()
    providers = await provider_service.get_available_providers()
    return {"providers": providers}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",
        "context_engine": settings.ENABLE_CONTEXT_ENGINE and settings.is_postgres()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)