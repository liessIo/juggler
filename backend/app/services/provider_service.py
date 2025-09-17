# backend/app/services/provider_service.py
"""
Provider service for managing AI providers
Phase 1: Only Ollama support
"""
from typing import Dict, Optional
from app.providers.base import BaseProvider, ContextPackage, ProviderResponse
from app.providers.ollama_adapter import OllamaAdapter
from app.config import settings


class ProviderService:
    """Service for managing AI providers"""
    
    def __init__(self):
        """Initialize provider service with available providers"""
        self.providers: Dict[str, BaseProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers based on configuration"""
        
        # Initialize Ollama (always available in Phase 1)
        if settings.ollama_base_url:
            self.providers["ollama"] = OllamaAdapter({
                "base_url": settings.ollama_base_url
            })
            print(f"✓ Ollama provider initialized at {settings.ollama_base_url}")
        
        # Phase 4: Add other providers here
        # if settings.groq_api_key:
        #     self.providers["groq"] = GroqAdapter({"api_key": settings.groq_api_key})
        
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
                is_available = await provider.health_check()
                models = await provider.list_models() if is_available else []
                
                result[name] = {
                    "available": is_available,
                    "models": models
                }
            except Exception as e:
                result[name] = {
                    "available": False,
                    "models": [],
                    "error": str(e)
                }
        
        # Add placeholders for future providers
        if "groq" not in result:
            result["groq"] = {"available": False, "models": []}
        if "gemini" not in result:
            result["gemini"] = {"available": False, "models": []}
            
        return result


# Global provider service instance (lazy initialization)
_provider_service = None

def get_provider_service() -> ProviderService:
    """Get or create the provider service instance"""
    global _provider_service
    if _provider_service is None:
        _provider_service = ProviderService()
    return _provider_service