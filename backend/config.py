"""
File: backend/config.py
Configuration Management for Juggler
Loads settings from environment variables and .env file
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Config:
    """Configuration settings for Juggler application"""
    
    # AI Provider API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Provider URLs
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Application Settings
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # CORS Settings
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    
    # Health Check Settings
    HEALTH_CHECK_CACHE_SECONDS = int(os.getenv("HEALTH_CHECK_CACHE_SECONDS", "30"))
    
    # Model Defaults
    DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))
    
    # Provider Timeouts (seconds)
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "30"))
    OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))
    
    @classmethod
    def is_gemini_configured(cls) -> bool:
        """Check if Gemini API key is configured"""
        return cls.GEMINI_API_KEY is not None and len(cls.GEMINI_API_KEY.strip()) > 0
    
    @classmethod
    def is_groq_configured(cls) -> bool:
        """Check if Groq API key is configured"""
        return cls.GROQ_API_KEY is not None and len(cls.GROQ_API_KEY.strip()) > 0
    
    @classmethod
    def is_openai_configured(cls) -> bool:
        """Check if OpenAI API key is configured"""
        return cls.OPENAI_API_KEY is not None and len(cls.OPENAI_API_KEY.strip()) > 0
    
    @classmethod
    def get_configured_providers(cls) -> list:
        """Get list of configured providers"""
        providers = ["ollama"]  # Ollama is always available if running
        
        if cls.is_gemini_configured():
            providers.append("gemini")
        
        if cls.is_groq_configured():
            providers.append("groq")
        
        if cls.is_openai_configured():
            providers.append("openai")
        
        return providers
    
    @classmethod
    def validate_config(cls) -> dict:
        """Validate configuration and return status"""
        issues = []
        warnings = []
        
        # Check if at least one cloud provider is configured
        if not cls.is_gemini_configured() and not cls.is_openai_configured():
            warnings.append("No cloud providers configured. Only Ollama will be available.")
        
        # Check URLs
        if not cls.OLLAMA_BASE_URL.startswith(("http://", "https://")):
            issues.append("OLLAMA_BASE_URL must start with http:// or https://")
        
        # Check numeric values
        if cls.PORT < 1 or cls.PORT > 65535:
            issues.append("PORT must be between 1 and 65535")
        
        if cls.DEFAULT_TEMPERATURE < 0 or cls.DEFAULT_TEMPERATURE > 2:
            warnings.append("DEFAULT_TEMPERATURE should be between 0 and 2")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "configured_providers": cls.get_configured_providers()
        }
    
    @classmethod
    def print_config_summary(cls):
        """Print configuration summary (without sensitive data)"""
        print("\n🔧 Juggler Configuration Summary")
        print("=" * 40)
        print(f"Debug Mode: {cls.DEBUG}")
        print(f"Host: {cls.HOST}:{cls.PORT}")
        print(f"Ollama URL: {cls.OLLAMA_BASE_URL}")
        
        providers = cls.get_configured_providers()
        print(f"Configured Providers: {', '.join(providers)}")
        
        print(f"Gemini: {'✅ Configured' if cls.is_gemini_configured() else '❌ Not configured'}")
        print(f"Groq: {'✅ Configured' if cls.is_groq_configured() else '❌ Not configured'}")
        print(f"OpenAI: {'✅ Configured' if cls.is_openai_configured() else '❌ Not configured'}")
        
        # Validation
        validation = cls.validate_config()
        if validation["issues"]:
            print("\n⚠️ Configuration Issues:")
            for issue in validation["issues"]:
                print(f"  • {issue}")
        
        if validation["warnings"]:
            print("\n💡 Warnings:")
            for warning in validation["warnings"]:
                print(f"  • {warning}")
        
        print("=" * 40 + "\n")

# Print config on import (only in debug mode)
if Config.DEBUG:
    Config.print_config_summary()