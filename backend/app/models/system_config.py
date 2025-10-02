# backend/app/models/config.py
"""Configuration model for system settings"""
from sqlalchemy import Column, String, JSON, DateTime
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database import Base

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    key = Column(String, primary_key=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get(cls, db: Session, key: str) -> Optional[Dict[str, Any]]:
        """Get a configuration value by key"""
        config = db.query(cls).filter(cls.key == key).first()
        if config:
            return {
                "key": config.key,
                "value": config.value,
                "updated_at": config.updated_at
            }
        return None
    
    @classmethod
    def set(cls, db: Session, key: str, value: Any) -> 'SystemConfig':
        """Set a configuration value"""
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
    def delete(cls, db: Session, key: str) -> bool:
        """Delete a configuration key"""
        config = db.query(cls).filter(cls.key == key).first()
        
        if config:
            db.delete(config)
            db.commit()
            return True
        
        return False
    
    @classmethod
    def get_all(cls, db: Session) -> Dict[str, Any]:
        """Get all configuration values"""
        configs = db.query(cls).all()
        return {
            config.key: config.value 
            for config in configs
        }