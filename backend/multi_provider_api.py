"""
File: backend/multi_provider_api.py
Juggler Multi-Provider AI Chat API
Supports Ollama (local), Groq (cloud), and Gemini (cloud) providers
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import time
import asyncio
from contextlib import asynccontextmanager

# Import config and AI libraries
from core.config import get_config
Config = get_config()

try:
    import google.generativeai as genai
    from google.generativeai.generative_models import GenerativeModel
    from google.generativeai.types import GenerationConfig
    GEMINI_AVAILABLE = True
    GEMINI_CONFIGURE_AVAILABLE = True
except ImportError as e:
    GEMINI_AVAILABLE = False
    GEMINI_CONFIGURE_AVAILABLE = False
    GenerativeModel = None
    GenerationConfig = None
    print(f"⚠️ google-generativeai not installed. Gemini provider will be disabled. Error: {e}")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️ groq not installed. Groq provider will be disabled.")

# Pydantic Models
class ChatRequest(BaseModel):
    message: str
    provider: str  # "ollama", "groq", or "gemini"
    model: Optional[str] = None  # auto-select if None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    conversation_history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    latency_ms: int
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    context_window: Optional[int] = None
    supports_vision: bool = False

class ProviderInfo(BaseModel):
    id: str
    name: str
    status: str  # "healthy", "degraded", "down", "not_configured"
    models: List[ModelInfo]
    latency_ms: Optional[int] = None

class ProvidersResponse(BaseModel):
    providers: List[ProviderInfo]
    total_models: int
    healthy_providers: int

# Global state
app_state = {
    "providers_status": {},
    "last_health_check": 0,
    "groq_client": None
}

# Health check functions
async def check_ollama_health() -> tuple[str, List[ModelInfo], Optional[int]]:
    """Check Ollama health and get models"""
    try:
        start_time = time.time()
        response = requests.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        latency_ms = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            models = []
            
            for model_data in data.get("models", []):
                model_name = model_data["name"]
                
                # Skip embedding models
                if "embed" in model_name.lower():
                    continue
                
                # Estimate context window based on model name
                context_window = 4096  # Default
                if "llama3" in model_name.lower():
                    context_window = 8192
                elif "mistral" in model_name.lower():
                    context_window = 8192
                elif "codellama" in model_name.lower():
                    context_window = 16384
                
                models.append(ModelInfo(
                    id=model_name,
                    name=model_name.replace(":", " ").title(),
                    provider="ollama",
                    context_window=context_window,
                    supports_vision="vision" in model_name.lower()
                ))
            
            return "healthy", models, latency_ms
        else:
            return "degraded", [], latency_ms
            
    except requests.exceptions.ConnectionError:
        return "down", [], None
    except Exception as e:
        print(f"Ollama health check error: {e}")
        return "down", [], None

async def check_gemini_health() -> tuple[str, List[ModelInfo], Optional[int]]:
    """Check Gemini health and get models"""
    if not Config.is_gemini_configured():
        return "not_configured", [], None
    
    if not GEMINI_AVAILABLE or not GEMINI_CONFIGURE_AVAILABLE or not GenerativeModel or not GenerationConfig:
        return "down", [], None
    
    try:
        start_time = time.time()
        
        # Test with a simple request
        model = GenerativeModel('gemini-pro')
        response = model.generate_content("Hi", 
            generation_config=GenerationConfig(
                max_output_tokens=1,
                temperature=0
            ))
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Define available Gemini models
        models = [
            ModelInfo(
                id="gemini-pro",
                name="Gemini Pro",
                provider="gemini",
                context_window=30720,  # ~30k tokens
                supports_vision=False
            ),
            ModelInfo(
                id="gemini-pro-vision",
                name="Gemini Pro Vision", 
                provider="gemini",
                context_window=30720,
                supports_vision=True
            )
        ]
        
        return "healthy", models, latency_ms
        
    except Exception as e:
        print(f"Gemini health check error: {e}")
        return "down", [], None

async def check_groq_health() -> tuple[str, List[ModelInfo], Optional[int]]:
    """Check Groq health and get models"""
    if not Config.is_groq_configured():
        return "not_configured", [], None
    
    if not GROQ_AVAILABLE or not app_state["groq_client"]:
        return "down", [], None
    
    try:
        start_time = time.time()
        
        # Test with a simple request
        client = app_state["groq_client"]
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1,
            temperature=0
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Define available Groq models (as of 2024)
        models = [
            ModelInfo(
                id="llama3-8b-8192",
                name="Llama 3 8B",
                provider="groq",
                context_window=8192,
                supports_vision=False
            ),
            ModelInfo(
                id="llama3-70b-8192",
                name="Llama 3 70B",
                provider="groq",
                context_window=8192,
                supports_vision=False
            ),
            ModelInfo(
                id="mixtral-8x7b-32768",
                name="Mixtral 8x7B",
                provider="groq",
                context_window=32768,
                supports_vision=False
            ),
            ModelInfo(
                id="gemma-7b-it",
                name="Gemma 7B IT",
                provider="groq",
                context_window=8192,
                supports_vision=False
            )
        ]
        
        return "healthy", models, latency_ms
        
    except Exception as e:
        print(f"Groq health check error: {e}")
        return "down", [], None

async def update_providers_status():
    """Update global provider status"""
    current_time = time.time()
    
    # Skip if checked recently (cache for 30 seconds)
    if current_time - app_state["last_health_check"] < 30:
        return
    
    print("🔍 Checking provider health...")
    
    # Check providers concurrently
    ollama_task = asyncio.create_task(check_ollama_health())
    gemini_task = asyncio.create_task(check_gemini_health())
    groq_task = asyncio.create_task(check_groq_health())
    
    ollama_status, ollama_models, ollama_latency = await ollama_task
    gemini_status, gemini_models, gemini_latency = await gemini_task
    groq_status, groq_models, groq_latency = await groq_task
    
    app_state["providers_status"] = {
        "ollama": {
            "status": ollama_status,
            "models": ollama_models,
            "latency_ms": ollama_latency
        },
        "gemini": {
            "status": gemini_status, 
            "models": gemini_models,
            "latency_ms": gemini_latency
        },
        "groq": {
            "status": groq_status,
            "models": groq_models,
            "latency_ms": groq_latency
        }
    }
    
    app_state["last_health_check"] = current_time
    
    healthy_count = sum(1 for p in app_state["providers_status"].values() if p["status"] == "healthy")
    total_models = sum(len(p["models"]) for p in app_state["providers_status"].values())
    
    print(f"✅ Health check complete: {healthy_count} healthy providers, {total_models} models available")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup providers"""
    print("🚀 Starting Juggler Multi-Provider API...")
    
    # Initialize Gemini if configured
    if Config.is_gemini_configured() and GEMINI_AVAILABLE and GEMINI_CONFIGURE_AVAILABLE:
        try:
            # Set API key via environment variable to avoid import issues
            import os
            if Config.GEMINI_API_KEY:  # Ensure it's not None
                os.environ['GOOGLE_API_KEY'] = Config.GEMINI_API_KEY
                print("✅ Gemini API key configured via environment")
            else:
                print("❌ Gemini API key is None")
        except Exception as e:
            print(f"❌ Gemini configuration failed: {e}")
    elif Config.is_gemini_configured():
        print("⚠️ Gemini API key provided but library not properly available")
    
    # Initialize Groq if configured
    if Config.is_groq_configured() and GROQ_AVAILABLE:
        try:
            app_state["groq_client"] = Groq(api_key=Config.GROQ_API_KEY)
            print("✅ Groq configured successfully")
        except Exception as e:
            print(f"❌ Groq configuration failed: {e}")
    elif Config.is_groq_configured():
        print("⚠️ Groq API key provided but library not available")
    
    # Initial health check
    await update_providers_status()
    
    yield
    
    # Cleanup
    print("🛑 Shutting down Juggler API...")

# FastAPI app
app = FastAPI(
    title="Juggler Multi-Provider API",
    description="Multi-Model AI Chat with seamless provider switching",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Juggler Multi-Provider AI Chat API", 
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    await update_providers_status()
    
    healthy_providers = sum(1 for p in app_state["providers_status"].values() if p["status"] == "healthy")
    total_providers = len(app_state["providers_status"])
    
    return {
        "status": "healthy" if healthy_providers > 0 else "degraded",
        "providers": f"{healthy_providers}/{total_providers}",
        "last_check": app_state["last_health_check"],
        "config": {
            "ollama_url": Config.OLLAMA_BASE_URL,
            "gemini_configured": Config.is_gemini_configured(),
            "groq_configured": Config.is_groq_configured(),
            "debug": Config.DEBUG
        }
    }

@app.get("/providers", response_model=ProvidersResponse)
async def get_providers():
    """Get all available providers and their models"""
    await update_providers_status()
    
    providers = []
    total_models = 0
    healthy_providers = 0
    
    for provider_id, provider_data in app_state["providers_status"].items():
        provider_name = provider_id.title()
        
        providers.append(ProviderInfo(
            id=provider_id,
            name=provider_name,
            status=provider_data["status"],
            models=provider_data["models"],
            latency_ms=provider_data["latency_ms"]
        ))
        
        total_models += len(provider_data["models"])
        if provider_data["status"] == "healthy":
            healthy_providers += 1
    
    return ProvidersResponse(
        providers=providers,
        total_models=total_models,
        healthy_providers=healthy_providers
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send message to specified AI provider"""
    
    # Validate provider
    if request.provider not in ["ollama", "gemini", "groq"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {request.provider}. Available: ollama, gemini, groq"
        )
    
    # Check provider status
    await update_providers_status()
    provider_status = app_state["providers_status"].get(request.provider, {})
    
    if provider_status.get("status") not in ["healthy", "degraded"]:
        status = provider_status.get("status", "unknown")
        raise HTTPException(
            status_code=503,
            detail=f"Provider '{request.provider}' is {status}"
        )
    
    # Route to appropriate handler
    if request.provider == "ollama":
        return await chat_ollama(request)
    elif request.provider == "gemini":
        return await chat_gemini(request)
    elif request.provider == "groq":
        return await chat_groq(request)

async def chat_ollama(request: ChatRequest) -> ChatResponse:
    """Handle Ollama chat request"""
    start_time = time.time()
    
    try:
        # Get available models
        available_models = app_state["providers_status"]["ollama"]["models"]
        if not available_models:
            raise HTTPException(status_code=503, detail="No Ollama models available")
        
        # Select model
        model = request.model or available_models[0].id
        
        # Validate model exists
        if not any(m.id == model for m in available_models):
            available_model_ids = [m.id for m in available_models]
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model}' not available. Available: {available_model_ids}"
            )
        
        # Prepare request with conversation history
        messages = []
        
        # Add conversation history if provided
        if request.conversation_history:
            for hist_msg in request.conversation_history:
                messages.append({
                    "role": hist_msg["role"],
                    "content": hist_msg["content"]
                })
        
        # Add current user message
        messages.append({
            "role": "user", 
            "content": request.message
        })

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature or 0.7,
                "num_predict": request.max_tokens or 2048
            }
        }
        
        # Send request
        response = requests.post(
            f"{Config.OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=120  # 2 minute timeout
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Ollama API error: {response.status_code} - {response.text}"
            )
        
        result = response.json()
        latency_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            response=result["message"]["content"],
            provider="ollama",
            model=model,
            latency_ms=latency_ms,
            input_tokens=result.get("prompt_eval_count"),
            output_tokens=result.get("eval_count")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        raise HTTPException(
            status_code=500,
            detail=f"Ollama chat failed after {latency_ms}ms: {str(e)}"
        )

async def chat_gemini(request: ChatRequest) -> ChatResponse:
    """Handle Gemini chat request"""
    start_time = time.time()
    
    try:
        if not Config.is_gemini_configured():
            raise HTTPException(status_code=400, detail="Gemini API key not configured")
        
        if not GEMINI_AVAILABLE or not GenerativeModel or not GenerationConfig:
            raise HTTPException(status_code=500, detail="Gemini library not available")
        
        # Get available models
        available_models = app_state["providers_status"]["gemini"]["models"]
        if not available_models:
            raise HTTPException(status_code=503, detail="No Gemini models available")
        
        # Select model  
        model_id = request.model or "gemini-pro"
        
        # Validate model
        if not any(m.id == model_id for m in available_models):
            available_model_ids = [m.id for m in available_models]
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model_id}' not available. Available: {available_model_ids}"
            )
        
        # Configure model
        model = GenerativeModel(model_id)
        
        # Build conversation context for Gemini
        # Gemini uses generate_content with a single prompt that includes history
        conversation_context = ""
        
        if request.conversation_history:
            for hist_msg in request.conversation_history:
                role_label = "Human" if hist_msg["role"] == "user" else "Assistant"
                conversation_context += f"{role_label}: {hist_msg['content']}\n\n"
        
        # Add current message
        conversation_context += f"Human: {request.message}\n\nAssistant:"
        
        generation_config = GenerationConfig(
            temperature=request.temperature or 0.7,
            max_output_tokens=request.max_tokens or 2048,
        )
        
        # Send request
        response = model.generate_content(
            conversation_context,
            generation_config=generation_config
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            response=response.text,
            provider="gemini",
            model=model_id,
            latency_ms=latency_ms,
            input_tokens=getattr(response, 'usage_metadata', {}).get('prompt_token_count', None),
            output_tokens=getattr(response, 'usage_metadata', {}).get('candidates_token_count', None)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        raise HTTPException(
            status_code=500,
            detail=f"Gemini chat failed after {latency_ms}ms: {str(e)}"
        )

async def chat_groq(request: ChatRequest) -> ChatResponse:
    """Handle Groq chat request"""
    start_time = time.time()
    
    try:
        if not Config.is_groq_configured():
            raise HTTPException(status_code=400, detail="Groq API key not configured")
        
        if not GROQ_AVAILABLE or not app_state["groq_client"]:
            raise HTTPException(status_code=500, detail="Groq client not available")
        
        # Get available models
        available_models = app_state["providers_status"]["groq"]["models"]
        if not available_models:
            raise HTTPException(status_code=503, detail="No Groq models available")
        
        # Select model
        model_id = request.model or "llama3-8b-8192"  # Default to Llama3 8B
        
        # Validate model
        if not any(m.id == model_id for m in available_models):
            available_model_ids = [m.id for m in available_models]
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model_id}' not available. Available: {available_model_ids}"
            )
        
        # Send request to Groq with conversation history
        client = app_state["groq_client"]
        
        # Build messages with conversation history
        messages = []
        
        # Add conversation history if provided
        if request.conversation_history:
            for hist_msg in request.conversation_history:
                messages.append({
                    "role": hist_msg["role"],
                    "content": hist_msg["content"]
                })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": request.message
        })

        completion = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=request.temperature or 0.7,
            max_tokens=request.max_tokens or 2048,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            response=completion.choices[0].message.content,
            provider="groq",
            model=model_id,
            latency_ms=latency_ms,
            input_tokens=completion.usage.prompt_tokens if completion.usage else None,
            output_tokens=completion.usage.completion_tokens if completion.usage else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        raise HTTPException(
            status_code=500,
            detail=f"Groq chat failed after {latency_ms}ms: {str(e)}"
        )

@app.post("/chat/switch")
async def switch_provider(current_provider: str, target_provider: str, message: str):
    """Switch between providers with context (placeholder for future context transfer)"""
    
    # For now, just send to target provider
    request = ChatRequest(
        message=message,
        provider=target_provider
    )
    
    response = await chat(request)
    
    if response is None:
        raise HTTPException(status_code=500, detail="Failed to get response from target provider")
    
    # Add metadata about the switch
    return {
        **response.model_dump(),
        "switched_from": current_provider,
        "context_transferred": False  # Will be True when we implement context transfer
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "multi_provider_api:app",  # Use import string for reload
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )