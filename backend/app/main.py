# backend/app/main.py

"""
Juggler API - Multi-provider AI Chat System with Security and Database
Complete main.py file with authentication, rate limiting, and SQLite database
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
import os
import json
import logging
from datetime import datetime, timedelta, timezone
import secrets
import uuid
from pathlib import Path

# Database imports
from app.database import (
    get_user_by_username,
    verify_user_password,
    create_user as db_create_user,
    init_db,
    create_conversation,
    add_message,
    get_conversation_messages,
    get_user_conversations
)

# Security imports
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, validator
import bleach
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Provider imports
import httpx
import ollama
from groq import Groq
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== Configuration ==============

class Settings:
    """Application settings"""
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Database
    DATABASE_PATH = Path("data")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
    RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

settings = Settings()
print(f"DEBUG: GROQ_API_KEY = '{settings.GROQ_API_KEY}'")
print(f"DEBUG: Key length = {len(settings.GROQ_API_KEY)}")

# ============== Security Setup ==============

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# ============== Pydantic Models ==============

class UserCreate(BaseModel):
    """User registration model"""
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @validator('username')
    def validate_username(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must contain only letters, numbers, underscore and hyphen')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        import re
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str

class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    user_id: Optional[str] = None

class MessageRequest(BaseModel):
    """Chat message request"""
    content: str = Field(..., min_length=1, max_length=10000)
    provider: str = Field(..., pattern="^(ollama|groq|gemini)$")
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    
    @validator('content')
    def sanitize_content(cls, v):
        """Sanitize message content"""
        return bleach.clean(v, tags=['p', 'br', 'strong', 'em', 'code', 'pre'], strip=True)

class ConversationResponse(BaseModel):
    """Conversation response model"""
    id: str
    title: Optional[str]
    messages: List[dict]
    created_at: datetime
    updated_at: datetime

# ============== Lifespan Events ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Juggler API...")
    
    # Initialize database
    init_db()
    
    # Create data directory if not exists
    settings.DATABASE_PATH.mkdir(exist_ok=True)
    
    # Initialize provider clients
    try:
        app.state.groq_client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
    except TypeError:
        # Fallback for library issues
        logger.warning("Could not initialize Groq client")
        app.state.groq_client = None
    
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Juggler API...")

# ============== FastAPI App ==============

app = FastAPI(
    title="Juggler API",
    description="Self-hosted multi-model AI chat with security",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# ============== Middleware ==============

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============== Authentication Functions ==============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request) -> TokenData:
    """Get current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Get token from header
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_exception
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
        
        if username is None:
            raise credentials_exception
            
        return TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception

# ============== Provider Functions ==============

async def get_ollama_response(prompt: str, model: str = "llama3:8b") -> str:
    """Get response from Ollama"""
    try:
        client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")

async def get_groq_response(prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    """Get response from Groq"""
    if not app.state.groq_client:
        raise HTTPException(status_code=500, detail="Groq API key not configured")
    
    try:
        print(f"DEBUG: Calling Groq with model: {model}, prompt: {prompt}")
        
        # Ensure model is valid
        if not model or model == "llama3-8b-8192":  # Old model
            model = "llama-3.1-8b-instant"  # Use new default
            
        chat_completion = app.state.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
        
        # Get response content
        response = chat_completion.choices[0].message.content if chat_completion.choices else None
        
        print(f"DEBUG: Groq raw response: {response}")
        
        # Handle empty response
        if not response or response.strip() == "":
            logger.warning(f"Empty response from Groq for model {model}")
            return f"Groq returned empty response. Model: {model} might be having issues. Please try another model."
        
        return response
        
    except Exception as e:
        logger.error(f"Groq error with model {model}: {e}")
        raise HTTPException(status_code=500, detail=f"Groq error: {str(e)}")

async def get_gemini_response(prompt: str, model_name: str = "gemini-pro") -> str:
    """Get response from Gemini"""
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")

# ============== API Endpoints ==============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Juggler API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

# ============== Authentication Endpoints ==============

@app.post("/api/auth/register", response_model=Token)
@limiter.limit("5/hour")
async def register(request: Request, user_data: UserCreate):
    """Register a new user"""
    try:
        # Create user in database
        user = db_create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        
        # Create tokens - user is a dict from db_create_user
        access_token = create_access_token(
            data={"sub": user_data.username, "user_id": user["id"]}
        )
        refresh_token = create_refresh_token(
            data={"sub": user_data.username, "user_id": user["id"]}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/api/auth/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, user_credentials: UserLogin):
    """Login user"""
    user = verify_user_password(user_credentials.username, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens using database user object
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.post("/api/auth/refresh", response_model=Token)
async def refresh_token(request: Request):
    """Refresh access token"""
    # Get refresh token from request
    refresh_token_str = request.headers.get("X-Refresh-Token")
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required"
        )
    
    try:
        payload = jwt.decode(refresh_token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        username = payload.get("sub")
        user_id = payload.get("user_id")
        
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Create new tokens
        access_token = create_access_token(
            data={"sub": username, "user_id": user_id}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": username, "user_id": user_id}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

# ============== Chat Endpoints ==============

@app.post("/api/chat/send")
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}seconds")
async def send_message(
    request: Request,
    message: MessageRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Send a message to AI provider"""
    try:
        # Create or get conversation
        if not message.conversation_id:
            conv = create_conversation(
                user_id=current_user.user_id,
                title=message.content[:50]
            )
            conversation_id = conv.id
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
        
        # Get response based on provider
        if message.provider == "ollama":
            response = await get_ollama_response(message.content, message.model or "llama3:8b")
        elif message.provider == "groq":
            response = await get_groq_response(message.content, message.model)
        elif message.provider == "gemini":
            response = await get_gemini_response(message.content, message.model or "gemini-pro")
        else:
            raise HTTPException(status_code=400, detail="Invalid provider")

        # Check if response is empty
        if not response:
            response = "Error: Provider returned empty response. Please try again or switch models."

        # Store assistant response
        add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response,  # Now guaranteed to have content
            provider=message.provider,
            model=message.model
        )
        
        return {
            "response": response,
            "conversation_id": conversation_id,
            "provider": message.provider,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/conversations")
async def get_conversations(
    current_user: TokenData = Depends(get_current_user)
):
    """Get user's conversations"""
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

@app.get("/api/chat/conversation/{conversation_id}")
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

# ============== Provider Status Endpoints ==============

@app.get("/api/providers/status")
@limiter.limit("60/minute")
async def get_providers_status(request: Request):
    """Get status of all providers"""
    status_dict = {}
    
    # Check Ollama
    try:
        client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        response = client.list()
        
        # Fix: response ist ein Objekt, nicht dict
        if hasattr(response, 'models'):
            status_dict["ollama"] = {
                "available": True,
                "models": [m.model for m in response.models]
            }
        else:
            models = response.get("models", []) if isinstance(response, dict) else []
            status_dict["ollama"] = {
                "available": len(models) > 0,
                "models": [m.get("name", m.get("model", "unknown")) for m in models]
            }
    except Exception as e:
        print(f"Ollama error: {e}")
        status_dict["ollama"] = {"available": False, "models": []}
    
    # Check Groq
    status_dict["groq"] = {
        "available": bool(settings.GROQ_API_KEY) and settings.GROQ_API_KEY != "your-encrypted-key",
        "models": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"] if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your-encrypted-key" else []
}
    
    # Check Gemini
    status_dict["gemini"] = {
        "available": bool(settings.GEMINI_API_KEY) and settings.GEMINI_API_KEY != "your-encrypted-key",
        "models": ["gemini-pro", "gemini-pro-vision"] if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your-encrypted-key" else []
    }
    
    return status_dict

# ============== WebSocket for Real-time Chat ==============

class ConnectionManager:
    """WebSocket connection manager"""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: str, client_id: str):
        if websocket := self.active_connections.get(client_id):
            await websocket.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Process message and send response
            await manager.send_personal_message(f"Echo: {data}", client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# ============== Admin Endpoints ==============

@app.get("/api/admin/stats")
async def get_admin_stats(
    current_user: TokenData = Depends(get_current_user)
):
    """Get admin statistics - requires admin role"""
    # Simple admin check - in production, check user role in database
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return {
        "total_users": "N/A",  # Would query database
        "total_conversations": "N/A",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)