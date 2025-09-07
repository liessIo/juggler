# backend/app/services/provider_service.py

"""
Provider service for managing AI model providers
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

import ollama
from groq import Groq
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

@dataclass
class ProviderStatus:
    available: bool
    models: List[str]
    last_refresh: datetime
    error: str = ""

class ModelCache:
    """Simple cache for provider models"""
    def __init__(self):
        self._cache: Dict[str, ProviderStatus] = {}
        self.TTL = settings.MODEL_CACHE_TTL
    
    def get(self, provider: str) -> ProviderStatus:
        """Get cached provider status"""
        return self._cache.get(provider, ProviderStatus(False, [], datetime.now()))
    
    def set(self, provider: str, status: ProviderStatus) -> None:
        """Cache provider status"""
        self._cache[provider] = status
    
    def is_expired(self, provider: str) -> bool:
        """Check if cache is expired"""
        if provider not in self._cache:
            return True
        
        age = (datetime.now() - self._cache[provider].last_refresh).seconds
        return age > self.TTL

class ProviderService:
    """Service for managing AI providers and their models"""
    
    def __init__(self):
        self.cache = ModelCache()
        self.groq_client = None
    
    async def initialize(self) -> None:
        """Initialize provider clients"""
        try:
            if settings.GROQ_API_KEY:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        except Exception as e:
            logger.warning(f"Could not initialize Groq client: {e}")
        
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Pre-load models
        await self.refresh_all_providers()
    
    def _fetch_ollama_models(self) -> List[str]:
        """Fetch models from Ollama - synchronous"""
        try:
            client = ollama.Client(host=settings.OLLAMA_BASE_URL)
            response = client.list()
            
            models: List[str] = []
            
            if hasattr(response, 'models'):
                for model in response.models:
                    if hasattr(model, 'model') and isinstance(model.model, str):
                        models.append(model.model)
            elif isinstance(response, dict) and 'models' in response:
                for model in response['models']:
                    if isinstance(model, dict):
                        name = model.get('name') or model.get('model')
                        if isinstance(name, str):
                            models.append(name)
            
            return models
        except Exception as e:
            logger.error(f"Error fetching Ollama models: {e}")
            return []
    
    def _fetch_groq_models(self) -> List[str]:
        """Fetch models from Groq - synchronous"""
        if not self.groq_client:
            return []
        
        try:
            response = self.groq_client.models.list()
            models: List[str] = []
            
            if hasattr(response, 'data'):
                for model in response.data:
                    if hasattr(model, 'id') and isinstance(model.id, str):
                        models.append(model.id)
            
            if not models:
                # Fallback to known models
                models = [
                    "llama-3.1-70b-versatile",
                    "llama-3.1-8b-instant",
                    "mixtral-8x7b-32768",
                    "gemma2-9b-it"
                ]
            
            return models
        except Exception as e:
            logger.error(f"Error fetching Groq models: {e}")
            return [
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
                "gemma2-9b-it"
            ]
    
    def _fetch_gemini_models(self) -> List[str]:
        """Fetch models from Gemini - synchronous"""
        if not settings.GEMINI_API_KEY:
            return []
        
        try:
            models_list = genai.list_models()
            models: List[str] = []
            
            for model in models_list:
                if hasattr(model, 'name') and hasattr(model, 'supported_generation_methods'):
                    name = model.name.split('/')[-1]
                    if isinstance(name, str) and 'generateContent' in model.supported_generation_methods:
                        models.append(name)
            
            if not models:
                models = ["gemini-pro", "gemini-pro-vision"]
            
            return models
        except Exception as e:
            logger.error(f"Error fetching Gemini models: {e}")
            return ["gemini-pro", "gemini-pro-vision"]
    
    async def refresh_provider(self, provider: str) -> ProviderStatus:
        """Refresh models for a specific provider"""
        logger.info(f"Refreshing models for {provider}")
        
        try:
            if provider == "ollama":
                models = await asyncio.to_thread(self._fetch_ollama_models)
            elif provider == "groq":
                models = await asyncio.to_thread(self._fetch_groq_models)
            elif provider == "gemini":
                models = await asyncio.to_thread(self._fetch_gemini_models)
            else:
                models = []
            
            status = ProviderStatus(
                available=len(models) > 0,
                models=models,
                last_refresh=datetime.now()
            )
            
            self.cache.set(provider, status)
            logger.info(f"Refreshed {len(models)} models for {provider}")
            return status
            
        except Exception as e:
            error_msg = f"Failed to refresh {provider}: {str(e)}"
            logger.error(error_msg)
            
            status = ProviderStatus(
                available=False,
                models=[],
                last_refresh=datetime.now(),
                error=error_msg
            )
            self.cache.set(provider, status)
            return status
    
    async def refresh_all_providers(self) -> Dict[str, ProviderStatus]:
        """Refresh all providers"""
        providers = ["ollama", "groq", "gemini"]
        results = await asyncio.gather(
            *[self.refresh_provider(p) for p in providers],
            return_exceptions=True
        )
        
        status_dict = {}
        for i, result in enumerate(results):
            provider = providers[i]
            if isinstance(result, Exception):
                status_dict[provider] = ProviderStatus(
                    available=False,
                    models=[],
                    last_refresh=datetime.now(),
                    error=str(result)
                )
            else:
                status_dict[provider] = result
        
        return status_dict
    
    async def get_provider_status(self, provider: str, force_refresh: bool = False) -> ProviderStatus:
        """Get provider status with optional refresh"""
        if force_refresh or self.cache.is_expired(provider):
            return await self.refresh_provider(provider)
        return self.cache.get(provider)
    
    async def get_all_providers(self, force_refresh: bool = False) -> Dict[str, ProviderStatus]:
        """Get status of all providers"""
        if force_refresh:
            return await self.refresh_all_providers()
        
        providers = ["ollama", "groq", "gemini"]
        return {p: self.cache.get(p) for p in providers}

# Global provider service instance
provider_service = ProviderService()