"""
Chat Models and Data Classes for Juggler
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import time

class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class ChatMessageModel(BaseModel):
    """Pydantic model for API requests/responses"""
    role: ChatRole
    content: str
    model_id: Optional[str] = None
    provider: Optional[str] = None
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatRequestModel(BaseModel):
    """API request for chat completion"""
    message: str
    conversation_id: str
    provider: str
    model_id: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

class ChatResponseModel(BaseModel):
    """API response for chat completion"""
    message: ChatMessageModel
    conversation_id: str
    provider_used: str
    model_used: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    finish_reason: str

class ParallelChatRequest(BaseModel):
    """Request for parallel queries to multiple providers"""
    message: str
    conversation_id: str
    providers: List[str]
    model_preferences: Optional[Dict[str, str]] = None  # provider -> model_id
    temperature: Optional[float] = 0.7

class ParallelChatResponse(BaseModel):
    """Response from parallel queries"""
    conversation_id: str
    results: List[ChatResponseModel]
    fastest_response_ms: int
    total_time_ms: int

class ProviderSwitchRequest(BaseModel):
    """Request to switch provider mid-conversation"""
    conversation_id: str
    new_provider: str
    new_model_id: str
    preserve_context: bool = True

class ConversationModel(BaseModel):
    """Conversation metadata"""
    id: str
    title: str
    created_at: float
    updated_at: float
    message_count: int
    last_message_preview: str
    primary_provider: str
    
class ProviderInfoModel(BaseModel):
    """Provider information"""
    id: str
    name: str
    status: str  # healthy, degraded, down
    models: List[Dict[str, Any]]
    features: Dict[str, bool] = Field(default_factory=dict)
    
class HealthCheckResponse(BaseModel):
    """System health check response"""
    status: str
    providers: List[ProviderInfoModel]
    active_conversations: int
    uptime_seconds: int