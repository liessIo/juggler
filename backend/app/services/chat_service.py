# backend/app/services/chat_service.py

"""
Chat service for handling AI provider interactions
"""

import asyncio
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.providers.ollama_adapter import OllamaAdapter
from app.providers.groq_adapter import GroqAdapter  
from app.providers.gemini_adapter import GeminiAdapter
from app.providers.base import ProviderStatus, CanonicalMessage, MessageRole

@dataclass
class ChatServiceResponse:
    content: str
    provider: str
    model: str
    latency_ms: int
    input_tokens: int = 0
    output_tokens: int = 0

class ChatService:
    """Service for managing chat interactions with AI providers"""
    
    def __init__(self):
        self.providers: Dict[str, Any] = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize chat service and providers"""
        if self.initialized:
            return
        
        try:
            # Import config with proper path
            from app.config import settings
            
            # Initialize Ollama (always try local)
            try:
                ollama = OllamaAdapter(settings.OLLAMA_BASE_URL)
                if await ollama.initialize():
                    self.providers["ollama"] = ollama
                    print("✅ Ollama adapter initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Ollama: {e}")
            
            # Initialize Groq if API key provided
            try:
                if settings.GROQ_API_KEY:
                    groq = GroqAdapter(settings.GROQ_API_KEY)
                    if await groq.initialize():
                        self.providers["groq"] = groq
                        print("✅ Groq adapter initialized")
                else:
                    print("⚠️ Groq API key not provided")
            except Exception as e:
                print(f"❌ Failed to initialize Groq: {e}")
            
            # Initialize Gemini if API key provided
            try:
                if settings.GEMINI_API_KEY:
                    gemini = GeminiAdapter(settings.GEMINI_API_KEY)
                    if await gemini.initialize():
                        self.providers["gemini"] = gemini
                        print("✅ Gemini adapter initialized")
                else:
                    print("⚠️ Gemini API key not provided")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini: {e}")
            
            self.initialized = True
            print(f"🚀 Chat service initialized with {len(self.providers)} providers")
            
        except Exception as e:
            print(f"💥 Chat service initialization failed: {e}")
            self.initialized = True  # Mark as initialized to prevent loops
    
    async def get_response(self, provider: str, model: Optional[str], prompt: str) -> str:
        """Get response from specified AI provider"""
        if not self.initialized:
            await self.initialize()
        
        if provider not in self.providers:
            available_providers = list(self.providers.keys())
            raise ValueError(f"Provider '{provider}' not available. Available: {available_providers}")
        
        provider_instance = self.providers[provider]
        
        # Create simple message for context package
        messages = [CanonicalMessage(role=MessageRole.USER, content=prompt)]
        
        # Select model if not provided
        if not model and provider_instance.models:
            model = provider_instance.models[0].model_id
        elif not model:
            raise ValueError(f"No models available for provider '{provider}'")
        
        # Create context package and send message
        context_package = provider_instance.create_context_package(messages, model, prompt)
        response = await provider_instance.send_message(context_package, model)
        
        return response.message.content

# Global service instance
chat_service = ChatService()