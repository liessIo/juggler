# backend/app/models/__init__.py

"""
Models module for Juggler application
Combines chat models and security models
"""

from sqlalchemy.ext.declarative import declarative_base

# Create the Base class for all models
Base = declarative_base()

# Import existing chat models
try:
    from .chat_models import *
except ImportError:
    pass  # chat_models might not have all models yet

# Import security models
from .security_models import (
    User,
    UserSession,
    APIKey,
    AuditLog,
    AuditEventType,
    Conversation,
)

# Export all models and Base for Alembic
__all__ = [
    # Base class
    'Base',
    
    # Security models
    'User',
    'UserSession',
    'APIKey',
    'AuditLog',
    'AuditEventType',
    'Conversation',
    
    # Add your chat_models exports here if needed
    # 'Message',
    # 'ChatSession',
    # etc.
]