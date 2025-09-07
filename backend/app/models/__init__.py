# backend/app/models/__init__.py

"""
Models package initialization - using existing comprehensive models
"""

# Use your existing models structure
from .security_models import (
    User,
    UserSession, 
    APIKey,
    AuditLog,
    AuditEventType,
    Conversation,
    Base
)

from .chat_models import (
    ChatRole,
    ChatMessageModel,
    ChatRequestModel,
    ChatResponseModel,
    ConversationModel,
    ProviderInfoModel
)

# Keep auth utilities separate for the refactored auth router
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