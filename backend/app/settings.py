"""
Application settings for Juggler v3 with Context Engine
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # App Settings
    APP_NAME: str = "Juggler AI Chat System"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./data/juggler.db",
        env="DATABASE_URL"
    )
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    # Provider API Keys
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        env="OLLAMA_BASE_URL"
    )
    GROQ_API_KEY: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Context Engine Settings
    CONTEXT_SHORT_TERM_LIMIT: int = Field(
        default=10,
        env="CONTEXT_SHORT_TERM_LIMIT",
        description="Number of recent messages to include in short-term memory"
    )
    
    CONTEXT_LONG_TERM_LIMIT: int = Field(
        default=5,
        env="CONTEXT_LONG_TERM_LIMIT",
        description="Number of semantically similar messages to retrieve"
    )
    
    CONTEXT_MAX_TOKENS: int = Field(
        default=4000,
        env="CONTEXT_MAX_TOKENS",
        description="Maximum tokens for context window"
    )
    
    SIMILARITY_THRESHOLD: float = Field(
        default=0.7,
        env="SIMILARITY_THRESHOLD",
        description="Minimum similarity score for message retrieval (0-1)"
    )
    
    # Embedding Settings
    EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL",
        description="Sentence transformer model for embeddings"
    )
    
    EMBEDDING_DIMENSION: int = Field(
        default=384,
        env="EMBEDDING_DIMENSION",
        description="Dimension of embedding vectors"
    )
    
    EMBEDDING_BATCH_SIZE: int = Field(
        default=32,
        env="EMBEDDING_BATCH_SIZE",
        description="Batch size for embedding generation"
    )
    
    # Circuit Breaker Settings
    CIRCUIT_BREAKER_THRESHOLD: int = Field(
        default=5,
        env="CIRCUIT_BREAKER_THRESHOLD",
        description="Number of failures before opening circuit"
    )
    
    CIRCUIT_BREAKER_TIMEOUT: int = Field(
        default=60,
        env="CIRCUIT_BREAKER_TIMEOUT",
        description="Seconds to wait before retrying after circuit opens"
    )
    
    # Performance Settings
    ENABLE_CONTEXT_ENGINE: bool = Field(
        default=True,
        env="ENABLE_CONTEXT_ENGINE",
        description="Enable Context Engine features (requires PostgreSQL)"
    )
    
    ENABLE_EMBEDDINGS: bool = Field(
        default=True,
        env="ENABLE_EMBEDDINGS",
        description="Enable automatic embedding generation"
    )
    
    ENABLE_CIRCUIT_BREAKER: bool = Field(
        default=True,
        env="ENABLE_CIRCUIT_BREAKER",
        description="Enable circuit breaker for provider resilience"
    )
    
    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    LOG_RETRIEVALS: bool = Field(
        default=True,
        env="LOG_RETRIEVALS",
        description="Log message retrievals for transparency"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL"""
        return self.DATABASE_URL.startswith("postgresql")
    
    def is_context_engine_available(self) -> bool:
        """Check if Context Engine can be enabled"""
        return self.is_postgres() and self.ENABLE_CONTEXT_ENGINE


# Create global settings instance
settings = Settings()

# Validate Context Engine availability
if settings.ENABLE_CONTEXT_ENGINE and not settings.is_postgres():
    print("⚠️  Warning: Context Engine requires PostgreSQL. Disabling Context Engine features.")
    settings.ENABLE_CONTEXT_ENGINE = False