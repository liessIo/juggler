# backend/app/models/security_models.py

"""
Security-related database models for Juggler application
Includes User, Session, API Key management, and Audit logging
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

# Import Base from __init__.py or create new one
try:
    from . import Base
except ImportError:
    Base = declarative_base()

def generate_uuid():
    """Generate a new UUID string"""
    return str(uuid.uuid4())

class User(Base):
    """
    User model with security features
    Handles authentication, authorization, and user management
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # Authentication fields
    username = Column(String(30), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # User status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Profile information (optional)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    preferences = Column(Text, nullable=True)  # JSON string for user preferences
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Security fields for login protection
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Two-factor authentication (for future implementation)
    two_factor_secret = Column(String(255), nullable=True)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    conversations = relationship(
        "Conversation", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    api_keys = relationship(
        "APIKey", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    sessions = relationship(
        "UserSession", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    audit_logs = relationship(
        "AuditLog", 
        back_populates="user",
        lazy="dynamic"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_email_password', 'email', 'hashed_password'),
        Index('idx_user_username_active', 'username', 'is_active'),
    )
    
    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', email='{self.email}')>"
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'last_login': self.last_login.isoformat() if self.last_login is not None else None,
        }

class UserSession(Base):
    """
    User session for JWT token management
    Tracks active sessions and refresh tokens
    """
    __tablename__ = "user_sessions"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # Foreign key to user
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Token storage
    refresh_token = Column(Text, unique=True, nullable=False, index=True)
    access_token_jti = Column(String(255), nullable=True, index=True)  # JWT ID for access token
    
    # Session validity
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_name = Column(String(255), nullable=True)  # e.g., "Chrome on MacOS"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'revoked'),
        Index('idx_session_token_lookup', 'refresh_token', 'revoked'),
    )
    
    def __repr__(self):
        return f"<UserSession(id='{self.id}', user_id='{self.user_id}', created_at='{self.created_at}')>"
    
    def is_valid(self):
        """Check if session is still valid"""
        return self.revoked is False and self.expires_at > datetime.utcnow()

class APIKey(Base):
    """
    Encrypted API key storage for external services
    Stores encrypted keys for Groq, Gemini, OpenAI, etc.
    """
    __tablename__ = "api_keys"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # Foreign key to user
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Provider information
    provider = Column(String(50), nullable=False, index=True)  # groq, gemini, openai, anthropic, etc.
    key_name = Column(String(255), nullable=True)  # Optional user-friendly name
    
    # Encrypted storage
    encrypted_key = Column(Text, nullable=False)
    encryption_salt = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)  # For duplicate detection
    
    # Usage tracking
    last_used = Column(DateTime, nullable=True)
    times_used = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    
    # Validation
    is_valid = Column(Boolean, default=True, nullable=False)
    validated_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # For temporary keys
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index('idx_apikey_user_provider', 'user_id', 'provider'),
        Index('idx_apikey_hash', 'key_hash'),
    )
    
    def __repr__(self):
        return f"<APIKey(id='{self.id}', provider='{self.provider}', user_id='{self.user_id}')>"
    
    def to_dict(self):
        """Convert to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'provider': self.provider,
            'key_name': self.key_name,
            'is_valid': self.is_valid,
            'last_used': self.last_used.isoformat() if self.last_used is not None else None,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
        }

class AuditLog(Base):
    """
    Security audit log for tracking important events
    Records login attempts, API key changes, permission changes, etc.
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # User reference (nullable for system events)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Event information
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, api_key_change, etc.
    event_category = Column(String(50), nullable=False, default="security")  # security, api, admin, etc.
    event_severity = Column(String(20), nullable=False, default="info")  # info, warning, error, critical
    
    # Event details
    event_data = Column(Text, nullable=True)  # JSON data with event details
    event_message = Column(Text, nullable=True)  # Human-readable message
    
    # Request information
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(255), nullable=True)  # For request tracing
    
    # Result
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'created_at'),
        Index('idx_audit_type_time', 'event_type', 'created_at'),
        Index('idx_audit_severity_time', 'event_severity', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id='{self.id}', event_type='{self.event_type}', user_id='{self.user_id}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'event_severity': self.event_severity,
            'event_message': self.event_message,
            'ip_address': self.ip_address,
            'success': self.success,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
        }

# Event type constants for audit logging
class AuditEventType:
    """Constants for audit event types"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # Session events
    SESSION_CREATE = "session_create"
    SESSION_REVOKE = "session_revoke"
    SESSION_EXPIRE = "session_expire"
    
    # API key events
    API_KEY_CREATE = "api_key_create"
    API_KEY_UPDATE = "api_key_update"
    API_KEY_DELETE = "api_key_delete"
    API_KEY_VALIDATE = "api_key_validate"
    
    # Security events
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # Admin events
    PERMISSION_CHANGE = "permission_change"
    USER_DELETE = "user_delete"
    USER_SUSPEND = "user_suspend"

# Conversation model needs to be imported or defined if not in chat_models.py
class Conversation(Base):
    """
    Conversation/Chat session
    Links to User for ownership
    """
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    
    # Metadata
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Provider tracking
    last_provider = Column(String(50), nullable=True)
    last_model = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Soft delete
    deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation(id='{self.id}', title='{self.title}', user_id='{self.user_id}')>"