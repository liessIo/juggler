# backend/app/services/provider_service.py
"""
Provider service for managing AI providers
Updated: Support für Ollama, Groq und Anthropic
"""
from typing import Dict, Optional
import logging
from sqlalchemy.orm import Session

from app.providers.base import BaseProvider, ContextPackage, ProviderResponse
from app.providers.ollama_adapter import OllamaAdapter
from app.providers.groq_adapter import GroqAdapter
from app.settings import settings
from app.database import get_db
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)


class ProviderService:
    """Service for managing AI providers with shared API keys"""
    
    def __init__(self):
        """Initialize provider service"""
        self.providers: Dict[str, BaseProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers based on configuration"""
        
        # Get database session for config
        db = next(get_db())
        try:
            # 1. Initialize Ollama (lokal, immer verfügbar wenn läuft)
            if settings.ollama_base_url:
                try:
                    ollama = OllamaAdapter({
                        "base_url": settings.ollama_base_url
                    })
                    # Add is_available method check
                    self.providers["ollama"] = ollama
                    logger.info(f"✅ Ollama provider initialized at {settings.ollama_base_url}")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize Ollama: {e}")
            
            # 2. Initialize Groq (Cloud Provider)
            groq_config = db.query(SystemConfig).filter(SystemConfig.key == "groq_api_key").first()
            if groq_config and groq_config.value:
                try:
                    groq = GroqAdapter({
                        "api_key": groq_config.value
                    })
                    if groq.is_available():
                        self.providers["groq"] = groq
                        logger.info("✅ Groq provider initialized")
                    else:
                        logger.warning("⚠️ Groq API key provided but provider not available")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize Groq: {e}")
            else:
                logger.info("ℹ️ No Groq API key configured")
            
            # 3. Initialize Anthropic (Cloud Provider)
            anthropic_config = db.query(SystemConfig).filter(SystemConfig.key == "anthropic_api_key").first()
            if anthropic_config and anthropic_config.value:
                try:
                    # Anthropic Adapter importieren
                    from app.providers.anthropic_adapter import AnthropicAdapter
                    anthropic = AnthropicAdapter({
                        "api_key": anthropic_config.value
                    })
                    if anthropic.is_available():
                        self.providers["anthropic"] = anthropic
                        logger.info("✅ Anthropic provider initialized")
                    else:
                        logger.warning("⚠️ Anthropic API key provided but provider not available")
                except ImportError:
                    logger.warning("⚠️ Anthropic adapter not found - needs to be created")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize Anthropic: {e}")
            else:
                logger.info("ℹ️ No Anthropic API key configured")
                
        finally:
            db.close()
        
        logger.info(f"Provider initialization complete. Active: {list(self.providers.keys())}")
    
    async def send_message(
        self,
        provider_name: str,
        model: str,
        messages: list,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ProviderResponse:
        """Send a message using the specified provider"""
        
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Provider '{provider_name}' not available")
        
        # Create context package
        context = ContextPackage(
            messages=messages,
            system_prompt=system_prompt,
            **kwargs  # temperature, max_tokens, etc.
        )
        
        return await provider.send_message(context, model)
    
    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get a provider by name"""
        return self.providers.get(name)
    
    async def get_available_providers(self) -> Dict:
        """Get information about available providers"""
        result = {}
        
        for name, provider in self.providers.items():
            try:
                # Use async health_check instead of is_available
                is_available = await provider.health_check()
                models = await provider.list_models() if is_available else []
                
                result[name] = {
                    "available": is_available,
                    "models": models
                }
            except Exception as e:
                logger.error(f"Error checking provider {name}: {e}")
                result[name] = {
                    "available": False,
                    "models": [],
                    "error": str(e)
                }
        
        # Add placeholders for non-initialized providers
        all_providers = ["ollama", "groq", "anthropic"]
        for provider_name in all_providers:
            if provider_name not in result:
                result[provider_name] = {
                    "available": False, 
                    "models": []
                }
            
        return result
    
    def refresh_providers(self):
        """Refresh provider configuration (z.B. nach API Key Update)"""
        logger.info("Refreshing providers...")
        self.providers.clear()
        self._initialize_providers()


# Global provider service instance
_provider_service = None


def get_provider_service() -> ProviderService:
    """Get or create the provider service instance"""
    global _provider_service
    if _provider_service is None:
        _provider_service = ProviderService()
    return _provider_service