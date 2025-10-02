# backend/app/config.py
"""
Configuration management for Juggler v2
Phase 1: Minimal configuration for Ollama
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    app_name: str = "Juggler v2"
    debug: bool = False
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    
    # Future: Other providers (not used in Phase 1)
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    # CORS settings
    cors_origins: list = ["http://localhost:5173"]
    
    class Config:
        env_file = "../.env"  # .env im Root-Verzeichnis
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignoriere unbekannte Variablen (wie VITE_*)

# Create global settings instance
settings = Settings()