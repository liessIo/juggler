# backend/app/models/schemas.py
"""
Pydantic schemas for request/response models
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None


# Message Variant schemas
class MessageVariantResponse(BaseModel):
    id: str
    original_message_id: str
    content: str
    provider: str
    model: str
    tokens_input: int
    tokens_output: int
    is_canonical: bool
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MessageVariantRequest(BaseModel):
    original_message_id: str
    provider: str
    model: str


class MessageVariantSelectRequest(BaseModel):
    variant_id: str
    original_message_id: str


# Chat schemas
class ChatRequest(BaseModel):
    message: str
    provider: str
    model: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    provider: str
    model: str
    tokens: Dict[str, int] = {}
    latency_ms: Optional[int] = None
    variants: List[MessageVariantResponse] = []


# Context schemas
class ContextMessageInfo(BaseModel):
    role: str
    content: str
    metadata: Optional[str] = None


class ContextSnapshotResponse(BaseModel):
    context_hash: str
    messages: List[ContextMessageInfo]
    temperature: float
    max_tokens: int
    metadata: Optional[Dict[str, Any]] = None


# Provider Health schemas
class ProviderHealthResponse(BaseModel):
    provider: str
    status: str  # "healthy", "degraded", "down"
    failure_count: int
    last_failure_at: Optional[str] = None
    opened_until: Optional[str] = None
    tokens_input_total: int = 0
    tokens_output_total: int = 0
    updated_at: Optional[str] = None


class ProvidersHealthResponse(BaseModel):
    providers: Dict[str, ProviderHealthResponse]


# Conversation schemas
class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    message_count: int = 0


# Message schemas
class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    provider: Optional[str] = None
    model: Optional[str] = None
    timestamp: Optional[str] = None


# Config schemas
class ConfigUpdate(BaseModel):
    groq_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    DELETE_groq_api_key: Optional[bool] = False
    DELETE_anthropic_api_key: Optional[bool] = False
    DELETE_openai_api_key: Optional[bool] = False


class ConfigResponse(BaseModel):
    groq_api_key: Optional[Dict[str, Any]] = None
    anthropic_api_key: Optional[Dict[str, Any]] = None
    openai_api_key: Optional[Dict[str, Any]] = None


# Provider schemas
class ModelInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    enabled: bool = True


class ProviderInfo(BaseModel):
    available: bool
    models: List[ModelInfo] = []


class ProvidersResponse(BaseModel):
    providers: Dict[str, ProviderInfo]