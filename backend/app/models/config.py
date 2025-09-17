# backend/app/models/config.py
"""Configuration model for system settings"""
from sqlalchemy import Column, String, JSON, DateTime
from datetime import datetime
from app.database import Base

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    key = Column(String, primary_key=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)