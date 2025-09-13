# backend/app/providers/groq_adapter.py

"""
Groq Provider Adapter for Juggler
Handles Groq cloud AI models with fast inference
"""

import time
from typing import List, Dict, Any, Optional

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None

from .base import (
    BaseProvider, CanonicalMessage, MessageRole, ModelInfo, 
    ContextPackage, ChatResponse, ProviderStatus, TokenBudget
)

class GroqAdapter(BaseProvider):
    """Provider adapter for Groq AI models"""
    
    def __init__(self, api_key: Optional[str]):
        super().__init__("groq")
        self.api_key = api_key
        self.client = None  # No type hint - simpler approach
        
    async def initialize(self) -> bool:
        """Initialize Groq connection"""
        if not GROQ_AVAILABLE:
            print("Groq library not available")
            self._status = ProviderStatus.DOWN
            return False
            
        if not self.api_key:
            print("Groq API key not provided")
            self._status = ProviderStatus.DOWN
            return False
            
        try:
            # Initialize Groq client with ONLY the api_key parameter
            # Avoid any proxy or httpx configurations that might cause issues
            self.client = Groq(api_key=self.api_key)
            
            # Get available models
            self._models = await self.get_available_models()
            
            # Test with simple request - check client is not None first
            if self._models and self.client is not None:
                try:
                    # Assert for type checker - we know client is not None here
                    assert self.client is not None
                    
                    # Find a safe model to test with (avoid TTS or special models)
                    test_model = "llama-3.1-8b-instant"  # Default safe model
                    for model in self._models:
                        if "llama" in model.model_id.lower() or "mixtral" in model.model_id.lower():
                            test_model = model.model_id
                            break
                    
                    response = self.client.chat.completions.create(
                        model=test_model,
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=1,
                        temperature=0
                    )
                    
                    self._status = ProviderStatus.HEALTHY
                    print(f"Groq adapter initialized successfully with {len(self._models)} models")
                    return True
                except Exception as test_error:
                    print(f"Groq test request failed: {test_error}")
                    self._status = ProviderStatus.DOWN
                    return False
            else:
                print("No Groq models available or client not initialized")
                self._status = ProviderStatus.DOWN
                return False
                
        except Exception as e:
            print(f"Groq initialization failed: {e}")
            self._status = ProviderStatus.DOWN
            return False
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of available Groq models"""
        if self.client is None:
            return []
            
        try:
            # Try to get models from API
            try:
                models_response = self.client.models.list()
                models = []
                
                if hasattr(models_response, 'data'):
                    for model in models_response.data:
                        if hasattr(model, 'id'):
                            # Determine model specs based on known models
                            model_id = model.id
                            context_window = 8192  # Default
                            max_tokens = 8192
                            
                            if "70b" in model_id.lower():
                                context_window = 8192
                                max_tokens = 8192
                            elif "8b" in model_id.lower():
                                context_window = 8192
                                max_tokens = 8192
                            elif "mixtral" in model_id.lower():
                                context_window = 32768
                                max_tokens = 32768
                            elif "gemma" in model_id.lower():
                                context_window = 8192
                                max_tokens = 8192
                            
                            models.append(ModelInfo(
                                model_id=model_id,
                                display_name=self._format_model_name(model_id),
                                context_window=context_window,
                                max_output_tokens=max_tokens,
                                supports_tools=False,  # Groq doesn't support function calling yet
                                supports_vision=False
                            ))
                
                if models:
                    print(f"Retrieved {len(models)} models from Groq API")
                    return models
            except Exception as api_error:
                print(f"Failed to get models from Groq API: {api_error}")
            
            # Fallback to known models if API doesn't return models
            print("Using fallback Groq models")
            return self._get_fallback_models()
            
        except Exception as e:
            print(f"Error in get_available_models: {e}")
            return self._get_fallback_models()
    
    def _get_fallback_models(self) -> List[ModelInfo]:
        """Fallback list of known Groq models"""
        return [
            ModelInfo(
                model_id="llama-3.1-8b-instant",
                display_name="Llama 3.1 8B Instant",
                context_window=131072,
                max_output_tokens=8192,
                supports_tools=False,
                supports_vision=False
            ),
            ModelInfo(
                model_id="llama-3.1-70b-versatile",
                display_name="Llama 3.1 70B Versatile",
                context_window=131072,
                max_output_tokens=8192,
                supports_tools=False,
                supports_vision=False
            ),
            ModelInfo(
                model_id="mixtral-8x7b-32768",
                display_name="Mixtral 8x7B",
                context_window=32768,
                max_output_tokens=32768,
                supports_tools=False,
                supports_vision=False
            ),
            ModelInfo(
                model_id="gemma2-9b-it",
                display_name="Gemma 2 9B IT",
                context_window=8192,
                max_output_tokens=8192,
                supports_tools=False,
                supports_vision=False
            )
        ]
    
    def _format_model_name(self, model_id: str) -> str:
        """Format model ID to display name"""
        name_mapping = {
            "llama-3.1-8b-instant": "Llama 3.1 8B Instant",
            "llama-3.1-70b-versatile": "Llama 3.1 70B Versatile",
            "mixtral-8x7b-32768": "Mixtral 8x7B",
            "gemma2-9b-it": "Gemma 2 9B IT"
        }
        return name_mapping.get(model_id, model_id.title())
    
    async def health_check(self) -> ProviderStatus:
        """Check Groq service health"""
        if self.client is None:
            print("Groq health check: client is None")
            return ProviderStatus.DOWN
            
        try:
            # Simple health check
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
                temperature=0
            )
            
            self._status = ProviderStatus.HEALTHY
            return ProviderStatus.HEALTHY
            
        except Exception as e:
            print(f"Groq health check failed: {e}")
            self._status = ProviderStatus.DOWN
            return ProviderStatus.DOWN
    
    def create_context_package(self, 
                             messages: List[CanonicalMessage],
                             target_model: str,
                             user_query: str = "") -> ContextPackage:
        """Create context package optimized for Groq models"""
        
        # Get model info for token budget
        model_info = next((m for m in self._models if m.model_id == target_model), None)
        max_tokens = model_info.context_window if model_info else 8192
        
        # Reserve tokens for response
        available_tokens = int(max_tokens * 0.75)
        budget = TokenBudget(available_tokens)
        
        # Extract facts from conversation
        facts = self._extract_facts(messages)
        
        # Create summary of older messages
        summary = self._create_summary(messages, budget.allocate("summary"))
        
        # Get recent messages that fit in budget
        recent_messages = self._get_recent_messages(messages, budget.allocate("recent"))
        
        # Create instruction optimized for Groq
        instruction = self._create_instruction(target_model)
        
        return ContextPackage(
            instruction=instruction,
            facts=facts,
            summary=summary,
            recent=recent_messages,
            user_query=user_query,
            metadata={
                "model_id": target_model,
                "provider": "groq",
                "context_window": max_tokens,
                "token_budget": available_tokens
            }
        )
    
    def serialize_context(self, context_package: ContextPackage, model_id: str) -> List[Dict[str, str]]:
        """Convert context package to Groq chat format"""
        messages = []
        
        # System message with instruction + facts + summary
        system_content = context_package.instruction
        
        if context_package.facts:
            facts_text = self._format_facts(context_package.facts)
            system_content += f"\n\nContext: {facts_text}"
        
        if context_package.summary:
            system_content += f"\n\nPrevious conversation: {context_package.summary}"
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # Add recent messages
        for msg in context_package.recent:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # Add current user query if provided
        if context_package.user_query:
            messages.append({
                "role": "user",
                "content": context_package.user_query
            })
        
        return messages
    
    async def send_message(self,
                          context_package: ContextPackage,
                          model_id: str,
                          **kwargs) -> ChatResponse:
        """Send message to Groq model"""
        start_time = time.time()
        
        if self.client is None:
            print(f"Groq send_message: client is None for model {model_id}")
            raise Exception("Groq client not initialized")
        
        try:
            # Serialize context to Groq format
            messages = self.serialize_context(context_package, model_id)
            
            # Send request to Groq
            response = self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
            )
            
            # Parse response
            message = self.parse_response(response, model_id)
            
            # Calculate metrics
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            # Get token usage from Groq response
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            
            return ChatResponse(
                message=message,
                provider="groq",
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                finish_reason=response.choices[0].finish_reason if response.choices else "stop",
                raw_response={
                    "usage": response.usage.model_dump() if response.usage else None,
                    "model": response.model
                }
            )
            
        except Exception as e:
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            print(f"Groq send_message error: {e}")
            
            # Return error response
            error_message = CanonicalMessage(
                role=MessageRole.ASSISTANT,
                content=f"Error: {str(e)}",
                metadata={"error": True}
            )
            
            return ChatResponse(
                message=error_message,
                provider="groq",
                model_id=model_id,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                finish_reason="error",
                raw_response={"error": str(e)}
            )
    
    def parse_response(self, raw_response: Any, model_id: str) -> CanonicalMessage:
        """Parse Groq response to canonical format"""
        
        content = ""
        if hasattr(raw_response, 'choices') and raw_response.choices:
            choice = raw_response.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                content = choice.message.content
        
        return CanonicalMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            metadata={
                "model_id": model_id,
                "provider": "groq",
                "finish_reason": raw_response.choices[0].finish_reason if raw_response.choices else "stop"
            }
        )
    
    def _extract_facts(self, messages: List[CanonicalMessage]) -> Dict[str, Any]:
        """Extract structured facts from conversation"""
        facts = {
            "entities": set(),
            "context_type": "general",
            "key_topics": set()
        }
        
        for message in messages:
            content = message.content.lower()
            
            # Detect context type
            if any(term in content for term in ["code", "programming", "function", "debug"]):
                facts["context_type"] = "technical"
            elif any(term in content for term in ["analyze", "data", "research"]):
                facts["context_type"] = "analytical"
            
            # Simple entity extraction
            words = content.split()
            for word in words:
                if word.istitle() and len(word) > 2:
                    facts["entities"].add(word)
        
        # Convert to lists for serialization
        facts["entities"] = list(facts["entities"])[:10]
        facts["key_topics"] = list(facts["key_topics"])[:5]
        
        return facts
    
    def _create_summary(self, messages: List[CanonicalMessage], token_budget: int) -> str:
        """Create conversation summary within token budget"""
        if len(messages) <= 5:
            return ""
        
        # Summarize middle section
        middle_start = max(0, len(messages) // 3)
        middle_end = max(middle_start, len(messages) - 5)
        middle_messages = messages[middle_start:middle_end]
        
        summary_points = []
        for msg in middle_messages[-3:]:  # Last 3 from middle section
            if msg.role == MessageRole.USER:
                summary_points.append(f"User: {msg.content[:80]}...")
            elif msg.role == MessageRole.ASSISTANT:
                summary_points.append(f"Assistant: {msg.content[:80]}...")
        
        summary = " | ".join(summary_points)
        return self.truncate_to_budget(summary, token_budget)
    
    def _get_recent_messages(self, messages: List[CanonicalMessage], token_budget: int) -> List[CanonicalMessage]:
        """Get recent messages that fit within token budget"""
        recent = []
        current_tokens = 0
        
        # Work backwards from most recent
        for message in reversed(messages):
            message_tokens = self.estimate_tokens(message.content)
            if current_tokens + message_tokens > token_budget:
                break
            
            recent.insert(0, message)
            current_tokens += message_tokens
        
        return recent
    
    def _create_instruction(self, model_id: str) -> str:
        """Create model-specific instruction"""
        base_instruction = "You are a helpful AI assistant. Provide accurate, concise, and helpful responses."
        
        if "instant" in model_id.lower():
            return base_instruction + " Keep responses focused and efficient."
        elif "versatile" in model_id.lower():
            return base_instruction + " You can handle complex, multi-faceted questions with detailed responses."
        elif "mixtral" in model_id.lower():
            return base_instruction + " Leverage your mixture-of-experts architecture for comprehensive responses."
        else:
            return base_instruction
    
    def _format_facts(self, facts: Dict[str, Any]) -> str:
        """Format facts for inclusion in prompt"""
        formatted = []
        
        if facts.get("entities"):
            formatted.append(f"Entities: {', '.join(facts['entities'])}")
        
        if facts.get("context_type"):
            formatted.append(f"Type: {facts['context_type']}")
        
        if facts.get("key_topics"):
            formatted.append(f"Topics: {', '.join(facts['key_topics'])}")
        
        return ". ".join(formatted)