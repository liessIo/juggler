"""
Juggler - Multi-Model AI Chat Application
FastAPI Backend Main Application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import asyncio

# Import our providers
try:
    # Try relative imports first
    from .providers.ollama_adapter import OllamaAdapter
    from .providers.base import CanonicalMessage, MessageRole
except ImportError:
    # Fallback to absolute imports
    from providers.ollama_adapter import OllamaAdapter
    from providers.base import CanonicalMessage, MessageRole

# Initialize FastAPI app
app = FastAPI(
    title="Juggler API",
    description="Multi-Model AI Chat Application with Context Transfer",
    version="1.0.0"
)

# Global provider instances
providers = {}

@app.on_event("startup")
async def startup_event():
    """Initialize providers on startup"""
    print("Initializing providers...")
    
    # Initialize Ollama
    ollama = OllamaAdapter()
    if await ollama.initialize():
        providers["ollama"] = ollama
        print(f"✅ Ollama initialized with {len(ollama.models)} models")
    else:
        print("❌ Ollama initialization failed")
        
    print(f"Total providers active: {len(providers)}")

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    for provider in providers.values():
        if hasattr(provider, 'close'):
            await provider.close()

# Initialize FastAPI app
app = FastAPI(
    title="Juggler API",
    description="Multi-Model AI Chat Application with Context Transfer",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
class ChatMessage(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    role: str  # user, assistant, system
    content: str
    model_id: Optional[str] = None
    provider: Optional[str] = None
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: str
    provider: str
    model_id: str

class ChatResponse(BaseModel):
    message: ChatMessage
    conversation_id: str
    provider_used: str
    latency_ms: int

class ConversationSummary(BaseModel):
    id: str
    title: str
    last_message: str
    message_count: int
    created_at: str
    updated_at: str

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Juggler API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "juggler-backend"}

# Provider endpoints
@app.get("/providers")
async def get_available_providers():
    """Get list of available AI providers and their status"""
    provider_info = []
    
    for name, provider in providers.items():
        status = await provider.health_check()
        models = [
            {
                "id": model.model_id,
                "name": model.display_name, 
                "context_window": model.context_window,
                "supports_tools": model.supports_tools,
                "supports_vision": model.supports_vision
            }
            for model in provider.models
        ]
        
        provider_info.append({
            "id": name,
            "name": provider.name.title(),
            "status": status.value,
            "models": models
        })
    
    return {"providers": provider_info}

# Chat endpoints
@app.post("/chat", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """Send a message to specified AI provider"""
    
    # Check if provider is available
    if request.provider not in providers:
        raise HTTPException(
            status_code=400, 
            detail=f"Provider '{request.provider}' not available. Active providers: {list(providers.keys())}"
        )
    
    provider = providers[request.provider]
    
    # Check if model is available
    available_models = [m.model_id for m in provider.models]
    if request.model_id not in available_models:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{request.model_id}' not available for {request.provider}. Available: {available_models}"
        )
    
    try:
        # For demo: create simple context with just the user message
        messages = [CanonicalMessage(
            role=MessageRole.USER,
            content=request.message
        )]
        
        # Create context package
        context_package = provider.create_context_package(
            messages=messages,
            target_model=request.model_id,
            user_query=request.message
        )
        
        # Send to provider
        chat_response = await provider.send_message(
            context_package=context_package,
            model_id=request.model_id,
            temperature=getattr(request, 'temperature', 0.7),
            max_tokens=getattr(request, 'max_tokens', 2048)
        )
        
        # Convert to API response format
        return ChatResponse(
            message=ChatMessage(
                role=chat_response.message.role.value,
                content=chat_response.message.content,
                model_id=request.model_id,
                provider=request.provider,
                timestamp=str(chat_response.message.timestamp)
            ),
            conversation_id=request.conversation_id,
            provider_used=chat_response.provider,
            latency_ms=chat_response.latency_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.post("/chat/parallel")
async def send_parallel_chat(request: ChatRequest, providers: List[str]):
    """Send same message to multiple providers for comparison"""
    # TODO: Implement parallel query functionality
    raise HTTPException(status_code=501, detail="Parallel chat not implemented yet")

# Conversation management
@app.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations():
    """Get list of user conversations"""
    # TODO: Implement conversation listing
    return []

@app.post("/conversations")
async def create_conversation():
    """Create new conversation"""
    # TODO: Implement conversation creation
    raise HTTPException(status_code=501, detail="Conversation creation not implemented yet")

@app.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get messages from specific conversation"""
    # TODO: Implement message retrieval
    raise HTTPException(status_code=501, detail="Message retrieval not implemented yet")

# Context transfer endpoints
@app.post("/conversations/{conversation_id}/switch-provider")
async def switch_provider(conversation_id: str, new_provider: str):
    """Switch to different provider while preserving context"""
    # TODO: Implement context transfer
    raise HTTPException(status_code=501, detail="Provider switching not implemented yet")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)