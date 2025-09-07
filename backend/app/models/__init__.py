# backend/app/models/__init__.py

"""
Models package initialization - fixed imports
"""

# Import Base first from security_models
from .security_models import (
    Base,
    User,
    UserSession, 
    APIKey,
    AuditLog,
    AuditEventType,
    Conversation
)

from .chat_models import (
    ChatRole,
    ChatMessageModel,
    ChatRequestModel,
    ChatResponseModel,
    ConversationModel,
    ProviderInfoModel,
    ParallelChatRequest,
    ParallelChatResponse,
    ProviderSwitchRequest,
    HealthCheckResponse
)

# Auth utilities - these need to be imported separately
from .auth_utils import (
    UserCreate,
    UserLogin, 
    Token,
    TokenData,
    get_current_user,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)

__all__ = [
    # Database models
    "Base",
    "User", 
    "UserSession",
    "APIKey",
    "AuditLog", 
    "AuditEventType",
    "Conversation",
    
    # Pydantic models
    "ChatRole",
    "ChatMessageModel", 
    "ChatRequestModel",
    "ChatResponseModel",
    "ConversationModel",
    "ProviderInfoModel",
    "ParallelChatRequest",
    "ParallelChatResponse", 
    "ProviderSwitchRequest",
    "HealthCheckResponse",
    
    # Auth utilities
    "UserCreate",
    "UserLogin",
    "Token", 
    "TokenData",
    "get_current_user",
    "verify_password",
    "get_password_hash", 
    "create_access_token",
    "create_refresh_token"
]