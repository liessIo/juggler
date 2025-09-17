# backend/app/providers/ollama_adapter.py
"""
Ollama provider adapter for Juggler v2
Handles communication with local Ollama instance
"""
import httpx
import json
from typing import Dict, List, Any, AsyncGenerator, Optional
from .base import BaseProvider, ContextPackage, ProviderResponse


class OllamaAdapter(BaseProvider):
    """Adapter for Ollama local models"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Ollama adapter with base URL"""
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.timeout = config.get("timeout", 60.0)
    
    async def send_message(
        self, 
        context_package: ContextPackage,
        model: str
    ) -> ProviderResponse:
        """Send a message to Ollama and get a response"""
        
        # Convert context package to Ollama format
        messages = context_package.messages
        
        # Add system prompt if provided
        if context_package.system_prompt:
            messages = [
                {"role": "system", "content": context_package.system_prompt}
            ] + messages
        
        # Prepare request
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": context_package.temperature,
                "top_p": context_package.top_p,
            }
        }
        
        if context_package.max_tokens:
            payload["options"]["num_predict"] = context_package.max_tokens
        
        # Send request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract token usage if available
                tokens_used = {
                    "input": data.get("prompt_eval_count", 0),
                    "output": data.get("eval_count", 0)
                }
                
                return ProviderResponse(
                    content=data["message"]["content"],
                    model=model,
                    provider="ollama",
                    tokens_used=tokens_used,
                    raw_response=data
                )
                
            except httpx.HTTPStatusError as e:
                raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                raise Exception(f"Ollama connection error: {str(e)}")
    
    async def stream_message(
        self, 
        context_package: ContextPackage,
        model: str
    ) -> AsyncGenerator[str, None]:
        """Stream a message response from Ollama"""
        
        messages = context_package.messages
        
        if context_package.system_prompt:
            messages = [
                {"role": "system", "content": context_package.system_prompt}
            ] + messages
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": context_package.temperature,
                "top_p": context_package.top_p,
            }
        }
        
        if context_package.max_tokens:
            payload["options"]["num_predict"] = context_package.max_tokens
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                            except json.JSONDecodeError:
                                continue
                                
            except httpx.HTTPStatusError as e:
                yield f"Error: {e.response.status_code}"
            except Exception as e:
                yield f"Error: {str(e)}"
    
    async def list_models(self) -> List[str]:
        """List available models from Ollama"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                
                # Extract model names
                models = [model["name"] for model in data.get("models", [])]
                return models
                
            except Exception as e:
                print(f"Failed to fetch Ollama models: {e}")
                return []
    
    async def health_check(self) -> bool:
        """Check if Ollama is available"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
            except Exception:
                return False
    
    def validate_model(self, model: str) -> bool:
        """Check if model exists in Ollama"""
        # For now, we'll accept any model name
        # Could be enhanced to check against list_models()
        return bool(model)