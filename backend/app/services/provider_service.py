# backend/app/services/provider_service.py

"""
Provider service for managing AI providers and their models
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from app.providers.ollama_adapter import OllamaAdapter
from app.providers.groq_adapter import GroqAdapter
from app.providers.gemini_adapter import GeminiAdapter
from app.providers.base import ProviderStatus

@dataclass
class ProviderServiceStatus:
    available: bool
    models: List[str]
    last_refresh: datetime
    error: Optional[str] = None

class ProviderService:
    """Service for managing AI providers"""
    
    def __init__(self):
        self.providers: Dict[str, any] = {}
        self.status_cache: Dict[str, ProviderServiceStatus] = {}
        self.cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
        self.initialized = False
    
    async def initialize(self):
        """Initialize provider service"""
        if self.initialized:
            return
        
        try:
            # Import config with proper path
            from app.config import settings
            
            # Initialize Ollama
            try:
                ollama = OllamaAdapter(settings.OLLAMA_BASE_URL)
                self.providers["ollama"] = ollama
                print("Ollama adapter registered")
            except Exception as e:
                print(f"Failed to register Ollama: {e}")
            
            # Initialize Groq if API key provided
            try:
                if settings.GROQ_API_KEY:
                    groq = GroqAdapter(settings.GROQ_API_KEY)
                    self.providers["groq"] = groq
                    print("Groq adapter registered")
                else:
                    print("Groq API key not provided")
            except Exception as e:
                print(f"Failed to register Groq: {e}")
            
            # Initialize Gemini if API key provided
            try:
                if settings.GEMINI_API_KEY:
                    gemini = GeminiAdapter(settings.GEMINI_API_KEY)
                    self.providers["gemini"] = gemini
                    print("Gemini adapter registered")
                else:
                    print("Gemini API key not provided")
            except Exception as e:
                print(f"Failed to register Gemini: {e}")
            
            self.initialized = True
            print(f"Provider service initialized with {len(self.providers)} providers")
            
        except Exception as e:
            print(f"Error initializing provider service: {e}")
            self.initialized = True  # Mark as initialized even if some fail
    
    async def get_all_providers(self) -> Dict[str, ProviderServiceStatus]:
        """Get status of all providers"""
        if not self.initialized:
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
    
    async def refresh_provider(self, provider_name: str) -> ProviderServiceStatus:
        """Refresh models for a specific provider"""
        if not self.initialized:
            await self.initialize()
        
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        
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
    
    async def refresh_all_providers(self) -> Dict[str, ProviderServiceStatus]:
        """Refresh all providers"""
        if not self.initialized:
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