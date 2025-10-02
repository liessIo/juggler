# backend/app/providers/anthropic_adapter.py
"""
Anthropic (Claude) provider adapter
"""
from typing import Dict, List, Optional, Any, AsyncGenerator
import logging
import httpx
from app.providers.base import BaseProvider, ContextPackage, ProviderResponse

logger = logging.getLogger(__name__)


class AnthropicAdapter(BaseProvider):
    """Adapter for Anthropic's Claude API"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic adapter with API key"""
        super().__init__(config)
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Available models - Anthropic verwendet spezifische Versionsnummern
        # Stand: Januar 2025
        self.available_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",  # Neueste Sonnet 3.5 Version
            "claude-3-5-haiku-20241022",   # Neueste Haiku 3.5 Version
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
    
    async def health_check(self) -> bool:
        """Check if Anthropic API is available"""
        try:
            # Simple check - try to get API info (will fail with 401 if key invalid)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/messages",  # This will return 405 but proves connection
                    headers=self.headers,
                    timeout=5.0
                )
                # 405 Method Not Allowed is expected for GET request
                # 401 would mean invalid API key
                return response.status_code != 401
        except Exception as e:
            logger.warning(f"Anthropic availability check failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """Synchronous availability check for initialization"""
        try:
            # Simple check - try to get API info (will fail with 401 if key invalid)
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/messages",  # This will return 405 but proves connection
                    headers=self.headers,
                    timeout=5.0
                )
                # 405 Method Not Allowed is expected for GET request
                # 401 would mean invalid API key
                return response.status_code != 401
        except Exception as e:
            logger.warning(f"Anthropic availability check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available Claude models"""
        # Anthropic hat keine Models-API, aber wir können testen welche funktionieren
        # Versuche mit einem einfachen Request zu testen welche Models verfügbar sind
        
        # Bekannte Models die wir testen können (Stand Januar 2025)
        test_models = [
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest", 
            "claude-3-opus-latest",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-instant-1.2"
        ]
        
        available = []
        for model in test_models:
            # Quick test mit minimalem Request
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/messages",
                        headers=self.headers,
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": "Hi"}],
                            "max_tokens": 1
                        },
                        timeout=5.0
                    )
                    if response.status_code != 404:
                        available.append(model)
            except:
                pass
        
        return available if available else ["claude-3-5-sonnet-latest"]  # Fallback
    
    async def send_message(self, context: ContextPackage, model: str) -> ProviderResponse:
        """Send message to Anthropic API"""
        if model not in self.available_models:
            # Try anyway - maybe new models are available
            logger.warning(f"Model {model} not in known list, trying anyway")
        
        # Convert messages to Anthropic format
        messages = self._convert_messages(context.messages)
        
        # Build request
        request_body = {
            "model": model,
            "messages": messages,
            "max_tokens": context.max_tokens or 4096,
            "temperature": context.temperature
        }
        
        # Add system prompt if provided
        if context.system_prompt:
            request_body["system"] = context.system_prompt
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=request_body,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract response
                content = data.get("content", [])
                response_text = ""
                if content and isinstance(content, list):
                    response_text = content[0].get("text", "")
                
                # Calculate tokens (Anthropic provides usage info)
                usage = data.get("usage", {})
                tokens_input = usage.get("input_tokens", 0)
                tokens_output = usage.get("output_tokens", 0)
                
                return ProviderResponse(
                    content=response_text,
                    model=model,
                    provider="anthropic",
                    tokens_used={
                        "input": tokens_input,
                        "output": tokens_output,
                        "total": tokens_input + tokens_output
                    }
                )
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Anthropic API error: {e.response.text}")
            raise Exception(f"Anthropic API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            raise
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert messages to Anthropic format"""
        converted = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Anthropic uses 'user' and 'assistant' roles
            if role in ["user", "assistant"]:
                converted.append({
                    "role": role,
                    "content": content
                })
            elif role == "system":
                # System messages should be set separately in Anthropic
                # Skip here as it's handled via system_prompt
                continue
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
        """Stream a message response from Anthropic"""
        # Convert messages to Anthropic format
        messages = self._convert_messages(context_package.messages)
        
        # Build request
        request_body = {
            "model": model,
            "messages": messages,
            "max_tokens": context_package.max_tokens or 4096,
            "temperature": context_package.temperature,
            "stream": True
        }
        
        # Add system prompt if provided
        if context_package.system_prompt:
            request_body["system"] = context_package.system_prompt
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=request_body,
                    timeout=30.0
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            import json
                            data = json.loads(line[6:])
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                    
        except Exception as e:
            logger.error(f"Error streaming from Anthropic: {e}")
            raise