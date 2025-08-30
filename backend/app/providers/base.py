"""
Base Provider Interface for Juggler Multi-Model Chat
Defines the standard interface all AI providers must implement
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time
import asyncio

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

@dataclass
class CanonicalMessage:
    """Standardized message format across all providers"""
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}

@dataclass  
class ModelInfo:
    """Information about available models"""
    model_id: str
    display_name: str
    context_window: int
    max_output_tokens: int
    supports_tools: bool = False
    supports_vision: bool = False

@dataclass
class ContextPackage:
    """Context transfer package between providers"""
    instruction: str          # System prompt
    facts: Dict[str, Any]     # Structured facts (never truncated)  
    summary: str             # Condensed conversation summary
    recent: List[CanonicalMessage]  # Recent messages
    user_query: str          # Current user question
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TokenBudget:
    """Token allocation for context transfer"""
    max_tokens: int
    instruction_ratio: float = 0.10    # 10% for system prompts
    facts_ratio: float = 0.20          # 20% for structured facts  
    summary_ratio: float = 0.30        # 30% for conversation summary
    recent_ratio: float = 0.30         # 30% for recent messages
    query_ratio: float = 0.10          # 10% for user query
    
    def allocate(self, component: str) -> int:
        """Calculate token allocation for component"""
        ratios = {
            "instruction": self.instruction_ratio,
            "facts": self.facts_ratio, 
            "summary": self.summary_ratio,
            "recent": self.recent_ratio,
            "query": self.query_ratio
        }
        return int(self.max_tokens * ratios.get(component, 0))

@dataclass
class ChatResponse:
    """Standardized response from providers"""
    message: CanonicalMessage
    provider: str
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    finish_reason: str
    raw_response: Optional[Dict[str, Any]] = None

class ProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    DOWN = "down"
    UNKNOWN = "unknown"

class BaseProvider(ABC):
    """Abstract base class for all AI providers"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self._models: List[ModelInfo] = []
        self._status: ProviderStatus = ProviderStatus.UNKNOWN
    
    @property
    def name(self) -> str:
        return self.provider_name
    
    @property
    def models(self) -> List[ModelInfo]:
        return self._models
    
    @property 
    def status(self) -> ProviderStatus:
        return self._status
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the provider and check availability"""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models from provider"""
        pass
    
    @abstractmethod
    async def health_check(self) -> ProviderStatus:
        """Check provider health and update status"""
        pass
        
    @abstractmethod
    def create_context_package(self, 
                             messages: List[CanonicalMessage],
                             target_model: str,
                             user_query: str = "") -> ContextPackage:
        """Create context package optimized for target model"""
        pass
    
    @abstractmethod
    def serialize_context(self, context_package: ContextPackage, model_id: str) -> Any:
        """Convert context package to provider-specific format"""
        pass
    
    @abstractmethod
    async def send_message(self,
                          context_package: ContextPackage, 
                          model_id: str,
                          **kwargs) -> ChatResponse:
        """Send message to AI model and return standardized response"""
        pass
    
    @abstractmethod 
    def parse_response(self, raw_response: Any, model_id: str) -> CanonicalMessage:
        """Parse provider response to canonical format"""
        pass
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (override with provider-specific tokenizer)"""
        # Very rough approximation: 1 token ≈ 4 characters
        return max(1, len(text) // 4)
    
    def truncate_to_budget(self, text: str, token_budget: int) -> str:
        """Truncate text to fit within token budget"""
        estimated_tokens = self.estimate_tokens(text)
        if estimated_tokens <= token_budget:
            return text
        
        # Rough truncation - keep from beginning
        chars_per_token = len(text) / estimated_tokens
        target_chars = int(token_budget * chars_per_token * 0.9)  # 10% safety margin
        
        if target_chars < len(text):
            return text[:target_chars] + "..."
        return text
    
    async def test_connection(self) -> bool:
        """Test if provider is accessible"""
        try:
            status = await self.health_check()
            return status != ProviderStatus.DOWN
        except Exception:
            return False