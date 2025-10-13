# backend/app/providers/groq_adapter.py
"""
Groq provider adapter
"""
from typing import Dict, List, Optional, Any, AsyncGenerator
import logging
from groq import Groq
from app.providers.base import BaseProvider, ContextPackage, ProviderResponse

logger = logging.getLogger(__name__)


class GroqAdapter(BaseProvider):
    """Adapter for Groq's API"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Groq adapter with API key"""
        super().__init__(config)
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("Groq API key is required")
        
        # Initialize Groq client (v0.31.1)
        self.client = Groq(api_key=self.api_key)
    
    async def health_check(self) -> bool:
        """Check if Groq API is available"""
        try:
            # Try to list models as health check
            models = self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"Groq availability check failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """Synchronous availability check for initialization"""
        try:
            models = self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"Groq availability check failed: {e}")
            return False
    
    async def list_models(self) -> List[Dict[str, str]]:
        """List available Groq models - returns dict format matching other adapters"""
        try:
            # Fetch models from API
            models_response = self.client.models.list()
            models = []
            
            for model in models_response.data:
                if hasattr(model, 'id'):
                    models.append({
                        "id": model.id,
                        "name": model.id,  # Groq doesn't provide separate display names
                        "description": f"Groq model: {model.id}"
                    })
            
            logger.info(f"Groq models fetched: {len(models)} models available")
            return sorted(models, key=lambda x: x["id"]) if models else []
            
        except Exception as e:
            logger.error(f"Error listing Groq models: {e}")
            return []
    
    async def send_message(self, context: ContextPackage, model: str) -> ProviderResponse:
        """Send message to Groq API"""
        
        # Convert messages to Groq format
        messages = self._convert_messages(context.messages)
        
        # Add system prompt if provided
        if context.system_prompt:
            messages.insert(0, {
                "role": "system",
                "content": context.system_prompt
            })
        
        try:
            # Groq SDK is synchronous, but we're in async context
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=context.temperature,
                max_tokens=context.max_tokens or 4096,
            )
            
            # Extract response
            response_text = response.choices[0].message.content
            
            # Get token usage
            usage = response.usage
            tokens_input = usage.prompt_tokens if usage else 0
            tokens_output = usage.completion_tokens if usage else 0
            
            return ProviderResponse(
                content=response_text,
                model=model,
                provider="groq",
                tokens_used={
                    "input": tokens_input,
                    "output": tokens_output,
                    "total": tokens_input + tokens_output
                }
            )
            
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            raise
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert messages to Groq format"""
        converted = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Groq uses standard OpenAI-style roles
            if role in ["user", "assistant", "system"]:
                converted.append({
                    "role": role,
                    "content": content
                })
            else:
                # Convert unknown roles to user
                converted.append({
                    "role": "user",
                    "content": content
                })
        
        return converted
    
    async def stream_message(
        self, 
        context_package: ContextPackage,
        model: str
    ) -> AsyncGenerator[str, None]:
        """Stream a message response from Groq"""
        # Convert messages to Groq format
        messages = self._convert_messages(context_package.messages)
        
        # Add system prompt if provided
        if context_package.system_prompt:
            messages.insert(0, {
                "role": "system",
                "content": context_package.system_prompt
            })
        
        try:
            # Groq supports streaming
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=context_package.temperature,
                max_tokens=context_package.max_tokens or 4096,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error streaming from Groq: {e}")
            raise