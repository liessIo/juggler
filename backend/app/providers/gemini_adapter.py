"""
Gemini Provider Adapter for Juggler
Handles Google Gemini AI models
"""

import time
from typing import List, Dict, Any, Optional

try:
    import google.generativeai as genai
    from google.generativeai.generative_models import GenerativeModel
    from google.generativeai.types import GenerationConfig
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    GenerativeModel = None
    GenerationConfig = None

from .base import (
    BaseProvider, CanonicalMessage, MessageRole, ModelInfo, 
    ContextPackage, ChatResponse, ProviderStatus, TokenBudget
)

class GeminiAdapter(BaseProvider):
    """Provider adapter for Google Gemini AI models"""
    
    def __init__(self, api_key: str):
        super().__init__("gemini")
        self.api_key = api_key
        self._configured = False
        
    async def initialize(self) -> bool:
        """Initialize Gemini connection"""
        if not GEMINI_AVAILABLE:
            print("Google Generative AI library not available")
            self._status = ProviderStatus.DOWN
            return False
            
        if not self.api_key:
            print("Gemini API key not provided")
            self._status = ProviderStatus.DOWN
            return False
            
        try:
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            self._configured = True
            
            # Get available models
            self._models = await self.get_available_models()
            
            # Test with simple request
            if self._models:
                test_model = GenerativeModel(self._models[0].model_id)
                response = test_model.generate_content(
                    "Hi",
                    generation_config=GenerationConfig(max_output_tokens=1, temperature=0)
                )
                
                self._status = ProviderStatus.HEALTHY
                return True
            else:
                self._status = ProviderStatus.DOWN
                return False
                
        except Exception as e:
            print(f"Gemini initialization failed: {e}")
            self._status = ProviderStatus.DOWN
            return False
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of available Gemini models"""
        if not self._configured:
            return []
            
        try:
            # Static list of known Gemini models
            # Dynamic model discovery is complex with Gemini API
            models = [
                ModelInfo(
                    model_id="gemini-pro",
                    display_name="Gemini Pro",
                    context_window=30720,
                    max_output_tokens=8192,
                    supports_tools=True,
                    supports_vision=False
                ),
                ModelInfo(
                    model_id="gemini-pro-vision",
                    display_name="Gemini Pro Vision",
                    context_window=30720,
                    max_output_tokens=8192,
                    supports_tools=False,
                    supports_vision=True
                ),
                ModelInfo(
                    model_id="gemini-1.5-pro",
                    display_name="Gemini 1.5 Pro",
                    context_window=1048576,  # 1M tokens
                    max_output_tokens=8192,
                    supports_tools=True,
                    supports_vision=True
                ),
                ModelInfo(
                    model_id="gemini-1.5-flash",
                    display_name="Gemini 1.5 Flash",
                    context_window=1048576,  # 1M tokens
                    max_output_tokens=8192,
                    supports_tools=True,
                    supports_vision=True
                )
            ]
            
            return models
            
        except Exception as e:
            print(f"Failed to get Gemini models: {e}")
            return []
    
    async def health_check(self) -> ProviderStatus:
        """Check Gemini service health"""
        if not self._configured:
            return ProviderStatus.DOWN
            
        try:
            # Simple health check with minimal request
            model = GenerativeModel('gemini-pro')
            response = model.generate_content(
                "Hi",
                generation_config=GenerationConfig(max_output_tokens=1, temperature=0)
            )
            
            self._status = ProviderStatus.HEALTHY
            return ProviderStatus.HEALTHY
            
        except Exception as e:
            print(f"Gemini health check failed: {e}")
            self._status = ProviderStatus.DOWN
            return ProviderStatus.DOWN
    
    def create_context_package(self, 
                             messages: List[CanonicalMessage],
                             target_model: str,
                             user_query: str = "") -> ContextPackage:
        """Create context package optimized for Gemini models"""
        
        # Get model info for token budget
        model_info = next((m for m in self._models if m.model_id == target_model), None)
        max_tokens = model_info.context_window if model_info else 30720
        
        # Reserve tokens for response
        available_tokens = int(max_tokens * 0.75)
        budget = TokenBudget(available_tokens)
        
        # Extract facts from conversation
        facts = self._extract_facts(messages)
        
        # Create summary of older messages
        summary = self._create_summary(messages, budget.allocate("summary"))
        
        # Get recent messages that fit in budget
        recent_messages = self._get_recent_messages(messages, budget.allocate("recent"))
        
        # Create instruction optimized for Gemini
        instruction = self._create_instruction(target_model)
        
        return ContextPackage(
            instruction=instruction,
            facts=facts,
            summary=summary,
            recent=recent_messages,
            user_query=user_query,
            metadata={
                "model_id": target_model,
                "provider": "gemini",
                "context_window": max_tokens,
                "token_budget": available_tokens
            }
        )
    
    def serialize_context(self, context_package: ContextPackage, model_id: str) -> str:
        """Convert context package to Gemini prompt format"""
        # Gemini uses a single prompt format
        prompt_parts = []
        
        # Add instruction
        if context_package.instruction:
            prompt_parts.append(f"Instructions: {context_package.instruction}")
        
        # Add facts
        if context_package.facts:
            facts_text = self._format_facts(context_package.facts)
            prompt_parts.append(f"Context: {facts_text}")
        
        # Add summary
        if context_package.summary:
            prompt_parts.append(f"Previous conversation: {context_package.summary}")
        
        # Add recent messages
        if context_package.recent:
            conversation_text = self._format_conversation(context_package.recent)
            prompt_parts.append(f"Recent messages:\n{conversation_text}")
        
        # Add current query
        if context_package.user_query:
            prompt_parts.append(f"User: {context_package.user_query}")
            prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    async def send_message(self,
                          context_package: ContextPackage,
                          model_id: str,
                          **kwargs) -> ChatResponse:
        """Send message to Gemini model"""
        start_time = time.time()
        
        if not self._configured:
            raise Exception("Gemini not configured")
        
        try:
            # Serialize context to Gemini format
            prompt = self.serialize_context(context_package, model_id)
            
            # Configure generation
            generation_config = GenerationConfig(
                temperature=kwargs.get("temperature", 0.7),
                max_output_tokens=kwargs.get("max_tokens", 2048),
            )
            
            # Create model instance
            model = GenerativeModel(model_id)
            
            # Send request
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Parse response
            message = self.parse_response(response, model_id)
            
            # Calculate metrics
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            # Estimate token usage
            input_tokens = self.estimate_tokens(prompt)
            output_tokens = self.estimate_tokens(message.content)
            
            return ChatResponse(
                message=message,
                provider="gemini",
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                finish_reason="stop",
                raw_response={"text": response.text}
            )
            
        except Exception as e:
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            # Return error response
            error_message = CanonicalMessage(
                role=MessageRole.ASSISTANT,
                content=f"Error: {str(e)}",
                metadata={"error": True}
            )
            
            return ChatResponse(
                message=error_message,
                provider="gemini",
                model_id=model_id,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                finish_reason="error",
                raw_response={"error": str(e)}
            )
    
    def parse_response(self, raw_response: Any, model_id: str) -> CanonicalMessage:
        """Parse Gemini response to canonical format"""
        
        content = raw_response.text if hasattr(raw_response, 'text') else str(raw_response)
        
        return CanonicalMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            metadata={
                "model_id": model_id,
                "provider": "gemini",
                "finish_reason": "stop"
            }
        )
    
    def _extract_facts(self, messages: List[CanonicalMessage]) -> Dict[str, Any]:
        """Extract structured facts from conversation"""
        facts = {
            "entities": set(),
            "topics": set(),
            "context_type": "general"
        }
        
        for message in messages:
            content = message.content.lower()
            
            # Detect context type
            if any(term in content for term in ["code", "programming", "function", "api"]):
                facts["context_type"] = "technical"
            elif any(term in content for term in ["write", "story", "creative", "poem"]):
                facts["context_type"] = "creative"
            
            # Simple entity extraction
            words = content.split()
            for word in words:
                if word.istitle() and len(word) > 2:
                    facts["entities"].add(word)
        
        # Convert to lists for serialization
        facts["entities"] = list(facts["entities"])[:10]
        facts["topics"] = list(facts["topics"])[:10]
        
        return facts
    
    def _create_summary(self, messages: List[CanonicalMessage], token_budget: int) -> str:
        """Create conversation summary within token budget"""
        if len(messages) <= 5:
            return ""
        
        # Summarize middle section
        middle_start = max(0, len(messages) // 3)
        middle_end = max(middle_start, len(messages) - 5)
        middle_messages = messages[middle_start:middle_end]
        
        summary_parts = []
        for msg in middle_messages[-5:]:  # Last 5 from middle section
            if msg.role == MessageRole.USER:
                summary_parts.append(f"User asked about: {msg.content[:100]}")
            elif msg.role == MessageRole.ASSISTANT:
                summary_parts.append(f"Assistant provided: {msg.content[:100]}")
        
        summary = ". ".join(summary_parts)
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
        base_instruction = "You are a helpful AI assistant. Provide clear, accurate, and helpful responses."
        
        if "vision" in model_id.lower():
            return base_instruction + " You can analyze and describe images when provided."
        elif "pro" in model_id.lower():
            return base_instruction + " Provide detailed, comprehensive responses leveraging your advanced capabilities."
        else:
            return base_instruction
    
    def _format_facts(self, facts: Dict[str, Any]) -> str:
        """Format facts for inclusion in prompt"""
        formatted = []
        
        if facts.get("entities"):
            formatted.append(f"Key entities: {', '.join(facts['entities'])}")
        
        if facts.get("context_type"):
            formatted.append(f"Context: {facts['context_type']}")
        
        return ". ".join(formatted)
    
    def _format_conversation(self, messages: List[CanonicalMessage]) -> str:
        """Format conversation for Gemini"""
        formatted = []
        
        for msg in messages:
            role = "User" if msg.role == MessageRole.USER else "Assistant"
            formatted.append(f"{role}: {msg.content}")
        
        return "\n".join(formatted)