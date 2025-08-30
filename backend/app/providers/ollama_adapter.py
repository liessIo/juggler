"""
Ollama Provider Adapter for Juggler
Handles local AI models via Ollama API
"""

import httpx
import json
import time
from typing import List, Dict, Any, Optional
from .base import (
    BaseProvider, CanonicalMessage, MessageRole, ModelInfo, 
    ContextPackage, ChatResponse, ProviderStatus, TokenBudget
)

class OllamaAdapter(BaseProvider):
    """Provider adapter for Ollama local AI models"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        super().__init__("ollama")
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for local models
        
    async def initialize(self) -> bool:
        """Initialize Ollama connection and discover available models"""
        try:
            # Test connection
            response = await self.client.get(f"{self.base_url}/api/version")
            if response.status_code != 200:
                self._status = ProviderStatus.DOWN
                return False
            
            # Get available models
            self._models = await self.get_available_models()
            self._status = ProviderStatus.HEALTHY
            return True
            
        except Exception as e:
            print(f"Ollama initialization failed: {e}")
            self._status = ProviderStatus.DOWN
            return False
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of installed Ollama models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                return []
            
            data = response.json()
            models = []
            
            for model_data in data.get("models", []):
                model_name = model_data["name"]
                
                # Extract model info from Ollama response
                # Context windows vary by model - using reasonable defaults
                context_window = 4096  # Default for most models
                if "llama2" in model_name.lower():
                    context_window = 4096
                elif "mistral" in model_name.lower():
                    context_window = 8192
                elif "codellama" in model_name.lower():
                    context_window = 16384
                elif "llama3" in model_name.lower():
                    context_window = 8192
                
                model_info = ModelInfo(
                    model_id=model_name,
                    display_name=model_name.title().replace(":", " "),
                    context_window=context_window,
                    max_output_tokens=2048,
                    supports_tools=False,  # Most local models don't support tools yet
                    supports_vision="vision" in model_name.lower()
                )
                models.append(model_info)
            
            return models
            
        except Exception as e:
            print(f"Failed to get Ollama models: {e}")
            return []
    
    async def health_check(self) -> ProviderStatus:
        """Check Ollama service health"""
        try:
            response = await self.client.get(f"{self.base_url}/api/version", timeout=5.0)
            if response.status_code == 200:
                self._status = ProviderStatus.HEALTHY
                return ProviderStatus.HEALTHY
            else:
                self._status = ProviderStatus.DEGRADED
                return ProviderStatus.DEGRADED
                
        except Exception:
            self._status = ProviderStatus.DOWN
            return ProviderStatus.DOWN
    
    def create_context_package(self, 
                             messages: List[CanonicalMessage],
                             target_model: str,
                             user_query: str = "") -> ContextPackage:
        """Create context package optimized for Ollama models"""
        
        # Get model info for token budget
        model_info = next((m for m in self._models if m.model_id == target_model), None)
        max_tokens = model_info.context_window if model_info else 4096
        
        # Reserve tokens for response (typically 25% of context window)
        available_tokens = int(max_tokens * 0.75)
        budget = TokenBudget(available_tokens)
        
        # Extract facts from conversation
        facts = self._extract_facts(messages)
        
        # Create summary of older messages
        summary = self._create_summary(messages, budget.allocate("summary"))
        
        # Get recent messages that fit in budget
        recent_messages = self._get_recent_messages(messages, budget.allocate("recent"))
        
        # Create instruction optimized for local models
        instruction = self._create_instruction(target_model)
        
        return ContextPackage(
            instruction=instruction,
            facts=facts,
            summary=summary, 
            recent=recent_messages,
            user_query=user_query,
            metadata={
                "model_id": target_model,
                "provider": "ollama",
                "context_window": max_tokens,
                "token_budget": available_tokens
            }
        )
    
    def serialize_context(self, context_package: ContextPackage, model_id: str) -> List[Dict[str, str]]:
        """Convert context package to Ollama chat format"""
        messages = []
        
        # System message with instruction + facts + summary
        system_content = context_package.instruction
        
        if context_package.facts:
            facts_text = self._format_facts(context_package.facts)
            system_content += f"\n\nImportant context:\n{facts_text}"
        
        if context_package.summary:
            system_content += f"\n\nConversation summary:\n{context_package.summary}"
        
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
        """Send message to Ollama model"""
        start_time = time.time()
        
        try:
            # Serialize context to Ollama format
            messages = self.serialize_context(context_package, model_id)
            
            # Prepare request
            payload = {
                "model": model_id,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 2048),
                }
            }
            
            # Send request to Ollama
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            raw_response = response.json()
            
            # Parse response
            message = self.parse_response(raw_response, model_id)
            
            # Calculate metrics
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            # Estimate token usage (Ollama doesn't provide exact counts)
            input_tokens = sum(self.estimate_tokens(msg["content"]) for msg in messages)
            output_tokens = self.estimate_tokens(message.content)
            
            return ChatResponse(
                message=message,
                provider="ollama",
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                finish_reason=raw_response.get("done_reason", "stop"),
                raw_response=raw_response
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
                provider="ollama", 
                model_id=model_id,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                finish_reason="error",
                raw_response={"error": str(e)}
            )
    
    def parse_response(self, raw_response: Dict[str, Any], model_id: str) -> CanonicalMessage:
        """Parse Ollama response to canonical format"""
        
        content = raw_response.get("message", {}).get("content", "")
        
        return CanonicalMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            metadata={
                "model_id": model_id,
                "provider": "ollama",
                "finish_reason": raw_response.get("done_reason", "stop"),
                "eval_count": raw_response.get("eval_count", 0),
                "eval_duration": raw_response.get("eval_duration", 0)
            }
        )
    
    def _extract_facts(self, messages: List[CanonicalMessage]) -> Dict[str, Any]:
        """Extract structured facts from conversation"""
        facts = {
            "entities": set(),
            "topics": set(), 
            "decisions": [],
            "context_type": "general"
        }
        
        # Simple fact extraction - can be enhanced with NLP
        for message in messages:
            content = message.content.lower()
            
            # Detect programming/technical context
            if any(term in content for term in ["code", "function", "python", "javascript", "api"]):
                facts["context_type"] = "technical"
            
            # Extract potential entities (very basic)
            words = content.split()
            for word in words:
                if word.istitle() and len(word) > 2:
                    facts["entities"].add(word)
        
        # Convert sets to lists for JSON serialization
        facts["entities"] = list(facts["entities"])[:10]  # Limit to top 10
        facts["topics"] = list(facts["topics"])[:10]
        
        return facts
    
    def _create_summary(self, messages: List[CanonicalMessage], token_budget: int) -> str:
        """Create conversation summary within token budget"""
        if len(messages) <= 5:
            return ""  # Don't summarize short conversations
        
        # Take middle section for summary (not too recent, not too old)
        middle_start = max(0, len(messages) // 3)
        middle_end = max(middle_start, len(messages) - 5)  # Leave last 5 for recent
        
        middle_messages = messages[middle_start:middle_end]
        
        # Create simple summary
        summary = "Previous discussion covered: "
        topics = set()
        
        for msg in middle_messages:
            if msg.role == MessageRole.USER:
                # Extract topics from user messages
                words = msg.content.lower().split()
                for word in words:
                    if len(word) > 4:  # Longer words more likely to be topics
                        topics.add(word)
        
        summary += ", ".join(list(topics)[:5])  # Top 5 topics
        
        # Truncate to budget
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
            
            recent.insert(0, message)  # Insert at beginning to maintain order
            current_tokens += message_tokens
        
        return recent
    
    def _create_instruction(self, model_id: str) -> str:
        """Create model-specific instruction"""
        base_instruction = "You are a helpful AI assistant. Continue the conversation naturally."
        
        # Model-specific optimizations
        if "code" in model_id.lower():
            return base_instruction + " Focus on providing accurate code examples and technical explanations."
        elif "instruct" in model_id.lower():
            return base_instruction + " Provide clear, step-by-step responses."
        else:
            return base_instruction
    
    def _format_facts(self, facts: Dict[str, Any]) -> str:
        """Format facts for inclusion in prompt"""
        formatted = []
        
        if facts.get("entities"):
            formatted.append(f"Key entities: {', '.join(facts['entities'])}")
        
        if facts.get("context_type"):
            formatted.append(f"Context type: {facts['context_type']}")
        
        if facts.get("decisions"):
            formatted.append(f"Decisions made: {', '.join(facts['decisions'])}")
        
        return "\n".join(formatted)
    
    async def close(self):
        """Clean up resources"""
        await self.client.aclose()