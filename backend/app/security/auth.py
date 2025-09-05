# backend/app/security/auth.py
"""
JWT Authentication and Authorization System for Juggler
Fixed version with proper type hints and error handling
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, validator
import secrets
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import hashlib
import hmac
import bleach

# ============== Configuration ==============
class SecurityConfig:
    """Security configuration settings"""
    SECRET_KEY = secrets.token_urlsafe(32)  # Should be from environment
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    PASSWORD_MIN_LENGTH = 8
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer
security = HTTPBearer()

# ============== MODELS ==============

class UserCreate(BaseModel):
    """User registration model with validation"""
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must contain only letters, numbers, underscore and hyphen')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < SecurityConfig.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {SecurityConfig.PASSWORD_MIN_LENGTH} characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
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
    scopes: list[str] = []

# ============== CORE FUNCTIONS ==============

class AuthService:
    """Main authentication service"""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self.failed_attempts: Dict[str, int] = {}
        self.lockout_until: Dict[str, datetime] = {}
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        encoded_jwt = jwt.encode(to_encode, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })
        encoded_jwt = jwt.encode(to_encode, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM)
        return encoded_jwt
    
    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user and return user data if valid"""
        # Check if user is locked out
        if username in self.lockout_until:
            if datetime.now() < self.lockout_until[username]:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Account locked. Try again after {self.lockout_until[username]}"
                )
            else:
                # Lockout expired, reset
                del self.lockout_until[username]
                self.failed_attempts[username] = 0
        
        # Get user from database (placeholder - implement your DB logic)
        user = await self.get_user(username)
        
        if not user:
            # Track failed attempt
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
            if self.failed_attempts[username] >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
                self.lockout_until[username] = datetime.now() + timedelta(
                    minutes=SecurityConfig.LOCKOUT_DURATION_MINUTES
                )
            return None
        
        if not self.verify_password(password, user['hashed_password']):
            # Track failed attempt
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
            if self.failed_attempts[username] >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
                self.lockout_until[username] = datetime.now() + timedelta(
                    minutes=SecurityConfig.LOCKOUT_DURATION_MINUTES
                )
            return None
        
        # Reset failed attempts on successful login
        self.failed_attempts[username] = 0
        return user
    
    async def get_user(self, username: str) -> Optional[dict]:
        """Get user from database - implement your logic here"""
        # Placeholder - connect to your database
        # Example:
        # if self.db:
        #     result = await self.db.execute(
        #         select(User).where(User.username == username)
        #     )
        #     user = result.scalar_one_or_none()
        #     return user.to_dict() if user else None
        return None
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SecurityConfig.SECRET_KEY, algorithms=[SecurityConfig.ALGORITHM])
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extrahiere Werte aus dem Payload
        username = payload.get("sub")
        user_id = payload.get("user_id")
        scopes = payload.get("scopes", [])
        
        # Prüfe ob username vorhanden ist (wichtig für Authentifizierung)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials - no username",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Stelle sicher dass scopes eine Liste ist
        if not isinstance(scopes, list):
            scopes = []
        
        # Return TokenData - username kann Optional[str] sein
        return TokenData(
            username=username,
            user_id=user_id,
            scopes=scopes
        )

# ============== DEPENDENCY INJECTION ==============

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    auth_service = AuthService(None)  # Pass your DB session here
    token_data = auth_service.verify_token(token)
    return token_data

async def require_scopes(*required_scopes):
    """Dependency to check if user has required scopes"""
    async def scope_checker(current_user: TokenData = Depends(get_current_user)):
        for scope in required_scopes:
            if scope not in current_user.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
        return current_user
    return scope_checker

# ============== API KEY MANAGEMENT ==============

class APIKeyManager:
    """Secure API Key Storage and Management"""
    
    def __init__(self):
        self.encryption_key = secrets.token_bytes(32)
    
    def encrypt_api_key(self, api_key: str, user_id: str) -> tuple[str, str]:
        """Encrypt API key for storage"""
        # Generate a unique salt for this key
        salt = secrets.token_bytes(16)
        
        # Derive encryption key from master key and salt
        key = hashlib.pbkdf2_hmac('sha256', self.encryption_key, salt, 100000)
        
        # Simple XOR encryption (use proper encryption library in production)
        encrypted = bytes(a ^ b for a, b in zip(api_key.encode(), key[:len(api_key)]))
        
        return encrypted.hex(), salt.hex()
    
    def decrypt_api_key(self, encrypted_key: str, salt: str) -> str:
        """Decrypt API key for use"""
        salt_bytes = bytes.fromhex(salt)
        encrypted_bytes = bytes.fromhex(encrypted_key)
        
        # Derive the same key
        key = hashlib.pbkdf2_hmac('sha256', self.encryption_key, salt_bytes, 100000)
        
        # Decrypt
        decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, key[:len(encrypted_bytes)]))
        return decrypted.decode()
    
    def validate_api_key_format(self, provider: str, api_key: str) -> bool:
        """Validate API key format for different providers"""
        patterns = {
            'groq': r'^gsk_[a-zA-Z0-9]{32,}$',
            'gemini': r'^AI[a-zA-Z0-9\-_]{35,}$',
            'openai': r'^sk-[a-zA-Z0-9]{48,}$',
            'anthropic': r'^sk-ant-[a-zA-Z0-9]{90,}$'
        }
        
        if provider not in patterns:
            return True  # Unknown provider, allow any format
        
        return bool(re.match(patterns[provider], api_key))

# ============== RATE LIMITING ==============

from collections import defaultdict
import asyncio

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: int = 30, per: int = 60):
        """
        Args:
            rate: Number of requests allowed
            per: Time window in seconds
        """
        self.rate = rate
        self.per = per
        self.allowance: defaultdict[str, float] = defaultdict(lambda: float(rate))  # Explizit als float
        self.last_check = defaultdict(datetime.now)
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(self, key: str) -> bool:
        """Check if request is within rate limit"""
        async with self._lock:
            now = datetime.now()
            time_passed = (now - self.last_check[key]).total_seconds()
            self.last_check[key] = now
            
            # Replenish tokens based on time passed
            self.allowance[key] += time_passed * (self.rate / self.per)
            
            # Cap at maximum rate
            if self.allowance[key] > self.rate:
                self.allowance[key] = self.rate
            
            # Check if request is allowed
            if self.allowance[key] < 1.0:
                return False
            else:
                self.allowance[key] -= 1.0
                return True

async def rate_limit_dependency(
    request_id: str,
    limiter: RateLimiter = Depends(lambda: RateLimiter())
):
    """Dependency for rate limiting"""
    if not await limiter.check_rate_limit(request_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    return True

# ============== INPUT VALIDATION & SANITIZATION ==============

class InputSanitizer:
    """Input validation and sanitization"""
    
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'code', 'pre']
    ALLOWED_ATTRIBUTES = {}
    
    @classmethod
    def sanitize_html(cls, content: str) -> str:
        """Remove dangerous HTML/scripts from user input"""
        return bleach.clean(
            content,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove any path components
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        # Allow only alphanumeric, dash, underscore, and dot
        filename = re.sub(r'[^a-zA-Z0-9\-_\.]', '', filename)
        # Limit length
        return filename[:255]
    
    @classmethod
    def validate_json_input(cls, data: Any, max_depth: int = 10) -> bool:
        """Validate JSON input to prevent deeply nested structures"""
        def check_depth(obj, current_depth=0):
            if current_depth > max_depth:
                return False
            if isinstance(obj, dict):
                return all(check_depth(v, current_depth + 1) for v in obj.values())
            elif isinstance(obj, list):
                return all(check_depth(item, current_depth + 1) for item in obj)
            return True
        
        return check_depth(data)

class MessageInput(BaseModel):
    """Validated message input model"""
    content: str = Field(..., min_length=1, max_length=10000)
    provider: str = Field(..., pattern="^(ollama|groq|gemini|openai|anthropic)$")
    conversation_id: Optional[str] = Field(None, pattern="^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")
    
    @validator('content')
    def sanitize_content(cls, v):
        """Sanitize message content"""
        return InputSanitizer.sanitize_html(v)
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Hello, how can you help me?",
                "provider": "groq",
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

# ============== CORS CONFIGURATION ==============

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

def setup_cors(app: FastAPI):
    """Configure CORS with security in mind"""
    origins = [
        "http://localhost:5173",  # Vue dev server
        "http://localhost:3000",  # Alternative dev port
        # Add your production domains here
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # Don't use ["*"] in production!
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )