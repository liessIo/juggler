# backend/app/providers/base.py
"""
Base provider interface for Juggler v2
Defines the contract all providers must implement
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator
from pydantic import BaseModel


class ContextPackage(BaseModel):
    """Package of context to send with a request"""
    messages: List[Dict[str, str]]
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class ProviderResponse(BaseModel):
    """Standard response from a provider"""
    content: str
    model: str
    provider: str
    tokens_used: Dict[str, int] = {"input": 0, "output": 0}
    raw_response: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """Abstract base class for all AI providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration"""
        self.config = config
        self.name = self.__class__.__name__.replace('Adapter', '').lower()
    
    @abstractmethod
    async def send_message(
        self, 
        context_package: ContextPackage,
        model: str
    ) -> ProviderResponse:
        """Send a message to the provider and get a response"""
        pass
    
    @abstractmethod
    async def stream_message(
        self, 
        context_package: ContextPackage,
        model: str
    ) -> AsyncGenerator[str, None]:
        """Stream a message response from the provider"""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models for this provider"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and responding"""
        pass
    
    def validate_model(self, model: str) -> bool:
        """Validate if a model is supported"""
        return True  # Default implementation, override if needed