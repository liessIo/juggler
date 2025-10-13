from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class SystemConfig(Base):
    """
    Store system-wide configuration like API keys
    """
    __tablename__ = "system_config"

    key = Column(String, primary_key=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def get(cls, db, key: str) -> Optional[Dict[str, Any]]:
        """Get a config value by key"""
        config = db.query(cls).filter(cls.key == key).first()
        return config.value if config else None

    @classmethod
    def set(cls, db, key: str, value: Any) -> 'SystemConfig':
        """Set a config value"""
        config = db.query(cls).filter(cls.key == key).first()
        if config:
            config.value = value
            config.updated_at = datetime.utcnow()
        else:
            config = cls(key=key, value=value)
            db.add(config)
        db.commit()
        return config

    @classmethod
    def delete(cls, db, key: str) -> bool:
        """Delete a config key"""
        config = db.query(cls).filter(cls.key == key).first()
        if config:
            db.delete(config)
            db.commit()
            return True
        return False


# Pydantic Models für API

class ProviderConfigSchema(BaseModel):
    """Schema for provider configuration"""
    api_key: Optional[str] = None
    active: bool = True
    last_used: Optional[datetime] = None


class ProviderConfigRequest(BaseModel):
    """Request schema for updating provider config"""
    groq: Optional[ProviderConfigSchema] = None
    anthropic: Optional[ProviderConfigSchema] = None
    openai: Optional[ProviderConfigSchema] = None
    ollama: Optional[ProviderConfigSchema] = None
    
    # For backwards compatibility - simple string API keys
    groq_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Delete flags (backwards compatibility)
    DELETE_groq_api_key: Optional[bool] = None
    DELETE_anthropic_api_key: Optional[bool] = None
    DELETE_openai_api_key: Optional[bool] = None


class ProviderConfigResponse(BaseModel):
    """Response schema for provider config"""
    exists: bool
    active: bool = True
    masked: Optional[str] = None
    last_used: Optional[str] = None