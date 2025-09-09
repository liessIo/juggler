# backend/app/services/provider_service.py

"""
Provider service for managing AI providers and their models
Now integrated with encrypted API key storage
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.providers.ollama_adapter import OllamaAdapter
from app.providers.groq_adapter import GroqAdapter
from app.providers.gemini_adapter import GeminiAdapter
from app.providers.base import ProviderStatus
from app.models.security_models import get_decrypted_api_key

@dataclass
class ProviderServiceStatus:
    available: bool
    models: List[str]
    last_refresh: datetime
    error: Optional[str] = None

class ProviderService:
    """Service for managing AI providers with encrypted key support"""
    
    def __init__(self):
        self.providers: Dict[str, Any] = {}
        self.status_cache: Dict[str, ProviderServiceStatus] = {}
        self.cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
        self.initialized = False
        self.current_user_id: Optional[str] = None
    
    def set_user_context(self, user_id: str):
        """Set the current user context for API key retrieval"""
        self.current_user_id = user_id
        # Clear providers when user changes to force re-initialization
        self.providers.clear()
        self.status_cache.clear()
        self.initialized = False
    
    async def initialize(self, user_id: Optional[str] = None):
        """Initialize provider service with user-specific API keys"""
        if user_id:
            self.set_user_context(user_id)
            
        if self.initialized and self.current_user_id:
            return
        
        try:
            # Import config for fallback values
            from app.config import settings
            
            # Initialize Ollama (uses base URL, no API key needed)
            try:
                ollama = OllamaAdapter(settings.OLLAMA_BASE_URL)
                self.providers["ollama"] = ollama
                print("Ollama adapter registered")
            except Exception as e:
                print(f"Failed to register Ollama: {e}")
            
            # Initialize Groq with encrypted API key
            try:
                if self.current_user_id:
                    # Try to get user's encrypted API key
                    try:
                        groq_key = get_decrypted_api_key(self.current_user_id, "groq")
                        groq = GroqAdapter(groq_key)
                        self.providers["groq"] = groq
                        print("Groq adapter registered with user API key")
                    except ValueError:
                        print("No Groq API key found for user")
                else:
                    # Fallback to environment variable for system-level operations
                    if settings.GROQ_API_KEY:
                        groq = GroqAdapter(settings.GROQ_API_KEY)
                        self.providers["groq"] = groq
                        print("Groq adapter registered with system API key")
                    else:
                        print("No Groq API key available")
            except Exception as e:
                print(f"Failed to register Groq: {e}")
            
            # Initialize Gemini with encrypted API key
            try:
                if self.current_user_id:
                    # Try to get user's encrypted API key
                    try:
                        gemini_key = get_decrypted_api_key(self.current_user_id, "gemini")
                        gemini = GeminiAdapter(gemini_key)
                        self.providers["gemini"] = gemini
                        print("Gemini adapter registered with user API key")
                    except ValueError:
                        print("No Gemini API key found for user")
                else:
                    # Fallback to environment variable for system-level operations
                    if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
                        gemini = GeminiAdapter(settings.GEMINI_API_KEY)
                        self.providers["gemini"] = gemini
                        print("Gemini adapter registered with system API key")
                    else:
                        print("No Gemini API key available")
            except Exception as e:
                print(f"Failed to register Gemini: {e}")
            
            self.initialized = True
            print(f"Provider service initialized with {len(self.providers)} providers for user {self.current_user_id}")
            
        except Exception as e:
            print(f"Error initializing provider service: {e}")
            self.initialized = True  # Mark as initialized even if some fail
    
    async def get_all_providers(self, user_id: Optional[str] = None) -> Dict[str, ProviderServiceStatus]:
        """Get status of all providers for a specific user"""
        if user_id and user_id != self.current_user_id:
            await self.initialize(user_id)
        elif not self.initialized:
            await self.initialize()
        
        # Check if we need to refresh cache
        now = datetime.now()
        results = {}
        
        for provider_name, provider_instance in self.providers.items():
            # Check cache first
            if (provider_name in self.status_cache and 
                now - self.status_cache[provider_name].last_refresh < self.cache_duration):
                results[provider_name] = self.status_cache[provider_name]
                continue
            
            # Refresh provider status
            try:
                status = await self._check_provider_status(provider_name, provider_instance)
                self.status_cache[provider_name] = status
                results[provider_name] = status
            except Exception as e:
                error_status = ProviderServiceStatus(
                    available=False,
                    models=[],
                    last_refresh=now,
                    error=str(e)
                )
                self.status_cache[provider_name] = error_status
                results[provider_name] = error_status
        
        return results
    
    async def refresh_provider(self, provider_name: str, user_id: Optional[str] = None) -> ProviderServiceStatus:
        """Refresh models for a specific provider"""
        if user_id and user_id != self.current_user_id:
            await self.initialize(user_id)
        elif not self.initialized:
            await self.initialize()
        
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found or not accessible for user {self.current_user_id}")
        
        provider_instance = self.providers[provider_name]
        
        try:
            # Force refresh
            status = await self._check_provider_status(provider_name, provider_instance, force_refresh=True)
            self.status_cache[provider_name] = status
            return status
        except Exception as e:
            error_status = ProviderServiceStatus(
                available=False,
                models=[],
                last_refresh=datetime.now(),
                error=str(e)
            )
            self.status_cache[provider_name] = error_status
            return error_status
    
    async def refresh_all_providers(self, user_id: Optional[str] = None) -> Dict[str, ProviderServiceStatus]:
        """Refresh all providers for a specific user"""
        if user_id and user_id != self.current_user_id:
            await self.initialize(user_id)
        elif not self.initialized:
            await self.initialize()
        
        results = {}
        
        # Refresh all providers concurrently
        tasks = []
        for provider_name in self.providers.keys():
            task = asyncio.create_task(self.refresh_provider(provider_name))
            tasks.append((provider_name, task))
        
        # Wait for all to complete
        for provider_name, task in tasks:
            try:
                status = await task
                results[provider_name] = status
            except Exception as e:
                results[provider_name] = ProviderServiceStatus(
                    available=False,
                    models=[],
                    last_refresh=datetime.now(),
                    error=str(e)
                )
        
        return results
    
    async def get_provider_for_user(self, provider_name: str, user_id: str):
        """Get a specific provider instance initialized with user's API keys"""
        if user_id != self.current_user_id:
            await self.initialize(user_id)
        elif not self.initialized:
            await self.initialize(user_id)
        
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not available for user {user_id}")
        
        return self.providers[provider_name]
    
    async def _check_provider_status(self, provider_name: str, provider_instance, force_refresh: bool = False) -> ProviderServiceStatus:
        """Check status of a provider"""
        now = datetime.now()
        
        try:
            # Initialize provider if needed
            if not hasattr(provider_instance, '_status') or provider_instance._status == ProviderStatus.UNKNOWN:
                await provider_instance.initialize()
            
            # Health check
            health_status = await provider_instance.health_check()
            
            if health_status == ProviderStatus.HEALTHY:
                # Get models
                if force_refresh or not provider_instance.models:
                    models = await provider_instance.get_available_models()
                    provider_instance._models = models
                
                model_names = [model.model_id for model in provider_instance.models]
                
                return ProviderServiceStatus(
                    available=True,
                    models=model_names,
                    last_refresh=now,
                    error=None
                )
            else:
                return ProviderServiceStatus(
                    available=False,
                    models=[],
                    last_refresh=now,
                    error=f"Provider health check failed: {health_status.value}"
                )
                
        except Exception as e:
            return ProviderServiceStatus(
                available=False,
                models=[],
                last_refresh=now,
                error=str(e)
            )

# Global service instance
provider_service = ProviderService()

# Helper function for easy access
async def get_user_provider_service(user_id: str) -> ProviderService:
    """Get provider service initialized for a specific user"""
    await provider_service.initialize(user_id)
    return provider_service