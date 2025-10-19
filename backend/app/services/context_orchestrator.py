# backend/app/services/context_orchestrator.py
"""
Context Orchestrator Service - The brain of the Context Engine
Manages intelligent context assembly, retrieval, and snapshots
"""

import hashlib
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import numpy as np
from sqlalchemy.orm import Session

from app.models.chat import Message, Conversation
from app.models.context_engine import (
    MessageEmbedding,
    RetrievalLog,
    ContextSnapshot,
    ProviderHealth
)
from app.providers.base import ContextPackage, ProviderResponse
from app.services.provider_service import get_provider_service
from app.settings import settings


@dataclass
class ProcessedResponse:
    """Response from context orchestrator"""
    response: str
    context_hash: str
    conversation_id: str
    message_id: str
    provider_used: str
    model_used: str
    tokens: Dict[str, int]
    retrieved_messages: List[Tuple[Message, float]]  # Message and similarity score
    latency_ms: int


class ContextOrchestrator:
    """
    Intelligent context management for conversations
    Handles short-term memory, long-term retrieval, and context assembly
    """
    
    def __init__(self):
        """Initialize the context orchestrator"""
        # Load embedding model (lazy loading to avoid startup delay)
        self._embedding_model = None
        self._embedding_queue = asyncio.Queue()
        self._is_initialized = False
        
        # Configuration
        self.short_term_limit = getattr(settings, 'CONTEXT_SHORT_TERM_LIMIT', 10)
        self.long_term_limit = getattr(settings, 'CONTEXT_LONG_TERM_LIMIT', 5)
        self.max_tokens = getattr(settings, 'CONTEXT_MAX_TOKENS', 4000)
        self.embedding_model_name = getattr(settings, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.similarity_threshold = getattr(settings, 'SIMILARITY_THRESHOLD', 0.7)
    
    @property
    def embedding_model(self):
        """Lazy load embedding model"""
        if self._embedding_model is None:
            print(f"Loading embedding model: {self.embedding_model_name}")
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model
    
    async def initialize(self):
        """Initialize the orchestrator and start background workers"""
        if not self._is_initialized:
            # Start embedding worker
            asyncio.create_task(self._embedding_worker())
            self._is_initialized = True
            print("Context Orchestrator initialized")
    
    async def process_message(
        self,
        db: Session,
        user_id: str,
        conversation_id: str,
        message: str,
        provider: str,
        model: str
    ) -> ProcessedResponse:
        """
        Main entry point for processing a message with intelligent context
        """
        print(f"DEBUG Context Orchestrator: provider={provider}, model={model}, message_type={type(message)}, message={message[:50] if isinstance(message, str) else message}")
        start_time = datetime.utcnow()
        
        # 1. Get or create conversation
        conversation = self._get_or_create_conversation(db, conversation_id, user_id)
        
        # 2. Get recent messages (short-term memory)
        recent_messages = self._get_recent_messages(db, conversation_id, self.short_term_limit)
        
        # 3. Perform semantic search if conversation is long enough (long-term memory)
        retrieved_messages = []
        if len(recent_messages) > 20:
            retrieved_messages = await self._semantic_search(
                db, message, conversation_id, self.long_term_limit
            )
        
        # 4. Assemble context package
        context_package = self._assemble_context(
            recent_messages,
            retrieved_messages,
            message,
            self.max_tokens
        )
        
        # 5. Calculate context hash
        context_hash = self._compute_context_hash(context_package)
        
        # 6. Check provider health and call with resilience
        response = await self._call_provider_with_resilience(
            db, provider, model, context_package
        )
        
        # 7. Save user message
        user_message = self._save_message(
            db, conversation.id, "user", message, None, None, 0, 0
        )
        
        # 8. Save assistant response
        assistant_message = self._save_message(
            db, conversation.id, "assistant", response.content,
            response.provider, response.model,
            response.tokens_used.get('input', 0),
            response.tokens_used.get('output', 0)
        )
        
        # 9. Save context snapshot
        self._save_context_snapshot(
            db, assistant_message.id, context_hash, context_package, {
                'provider': response.provider,
                'model': response.model,
                'temperature': context_package.temperature,
                'max_tokens': context_package.max_tokens
            }
        )
        
        # 10. Queue messages for embedding generation
        await self._embedding_queue.put((user_message.id, message))
        await self._embedding_queue.put((assistant_message.id, response.content))
        
        # 11. Log retrievals if any
        if retrieved_messages:
            turn_id = len(recent_messages) + 1
            for msg, score in retrieved_messages:
                RetrievalLog.log_retrieval(
                    db, conversation.id, turn_id, msg.id, score,
                    f"Semantic similarity: {score:.3f}"
                )
        
        # Calculate latency
        latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return ProcessedResponse(
            response=response.content,
            context_hash=context_hash,
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            provider_used=response.provider,
            model_used=response.model,
            tokens=response.tokens_used,
            retrieved_messages=retrieved_messages,
            latency_ms=latency_ms
        )
    
    def _get_or_create_conversation(
        self, db: Session, conversation_id: Optional[str], user_id: str
    ) -> Conversation:
        """Get existing conversation or create new one"""
        if conversation_id:
            conv = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
            if conv:
                print(f"DEBUG: Found existing conversation {conv.id}")
                return conv
        
        # Create new conversation
        conv = Conversation(
            user_id=user_id,
            title=f"New Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        print(f"DEBUG: Created new conversation with ID: {conv.id}, user_id: {conv.user_id}")
        return conv
    
    def _get_recent_messages(
        self, db: Session, conversation_id: str, limit: int
    ) -> List[Message]:
        """Get recent messages from the conversation"""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp.desc()).limit(limit).all()[::-1]
    
    async def _semantic_search(
        self, db: Session, query: str, conversation_id: str, top_k: int
    ) -> List[Tuple[Message, float]]:
        """
        Perform semantic search to find relevant messages
        """
        # Generate embedding for query
        query_embedding = await asyncio.to_thread(
            self.embedding_model.encode, query
        )
        
        # Search for similar messages
        similar_messages = MessageEmbedding.search_similar(
            db, query_embedding.tolist(), conversation_id, top_k, self.similarity_threshold
        )
        
        return similar_messages
    
    def _assemble_context(
        self,
        recent_messages: List[Message],
        retrieved_messages: List[Tuple[Message, float]],
        current_message: str,
        max_tokens: int
    ) -> ContextPackage:
        """
        Assemble context package from recent and retrieved messages
        ContextPackage.messages expects List[Dict[str, str]] - all values must be strings
        """
        context_messages = []
        
        # Add retrieved messages first (older context)
        for msg, score in retrieved_messages:
            # Serialize metadata to JSON string to comply with Dict[str, str] schema
            metadata_str = json.dumps({
                "retrieved": True,
                "similarity": float(score),
                "timestamp": msg.timestamp.isoformat()
            })
            context_messages.append({
                "role": msg.role,
                "content": msg.content,
                "metadata": metadata_str
            })
        
        # Add recent messages
        for msg in recent_messages:
            # Serialize metadata to JSON string
            metadata_str = json.dumps({
                "timestamp": msg.timestamp.isoformat()
            })
            context_messages.append({
                "role": msg.role,
                "content": msg.content,
                "metadata": metadata_str
            })
        
        # Add current message
        context_messages.append({
            "role": "user",
            "content": current_message
        })
        
        # Implement token counting and truncation
        # (1 token ≈ 4 characters)
        total_chars = sum(len(msg["content"]) for msg in context_messages)
        if total_chars > max_tokens * 4:
            # Truncate older messages if needed
            while total_chars > max_tokens * 4 and len(context_messages) > 1:
                removed = context_messages.pop(0)
                total_chars -= len(removed["content"])
        
        return ContextPackage(
            messages=context_messages,
            temperature=0.7,  # Default, could be configurable
            max_tokens=max_tokens
        )
    
    def _compute_context_hash(self, context_package: ContextPackage) -> str:
        """Compute SHA256 hash of context for reproducibility"""
        # Serialize context package to JSON
        context_json = json.dumps({
            "messages": context_package.messages,
            "temperature": context_package.temperature,
            "max_tokens": context_package.max_tokens
        }, sort_keys=True, default=str)
        
        # Compute hash
        return hashlib.sha256(context_json.encode()).hexdigest()
    
    async def _call_provider_with_resilience(
        self,
        db: Session,
        provider: str,
        model: str,
        context_package: ContextPackage
    ) -> ProviderResponse:
        """
        Call provider with circuit breaker pattern
        """
        # Check provider health
        health = ProviderHealth.get_status(db, provider)
        
        if not health.is_available():
            # Try failover to another provider
            return await self._failover_to_backup_provider(
                db, context_package, provider
            )
        
        try:
            # Call the provider
            response = await get_provider_service().send_message(
                provider_name=provider,
                model=model,
                messages=context_package.messages,
                system_prompt=context_package.system_prompt
            )
            
            # Record success
            ProviderHealth.record_success(db, provider)
            
            return response
            
        except Exception as e:
            print(f"Context Orchestrator error: {e}")
            # Record failure
            ProviderHealth.record_failure(db, provider)
            
            # Try failover
            return await self._failover_to_backup_provider(
                db, context_package, provider, str(e)
            )
    
    async def _failover_to_backup_provider(
        self,
        db: Session,
        context_package: ContextPackage,
        failed_provider: str,
        error: Optional[str] = None
    ) -> ProviderResponse:
        """
        Failover to a backup provider when primary fails
        """
        # Get list of available providers
        providers = await get_provider_service().get_available_providers()
        
        # Try each provider in order
        for backup_provider in providers:
            if backup_provider == failed_provider:
                continue
            
            health = ProviderHealth.get_status(db, backup_provider)
            if not health.is_available():
                continue
            
            try:
                # Get first available model for backup provider
                models = providers[backup_provider].get('models', [])
                if not models:
                    continue
                
                model = models[0] if isinstance(models[0], str) else models[0].get('id')
                
                response = await get_provider_service().send_message(
                    provider_name=backup_provider,
                    model=model,
                    messages=context_package.messages,
                    system_prompt=context_package.system_prompt
                )
                
                # Add failover info to response
                response.metadata = response.metadata or {}
                response.metadata['failover'] = True
                response.metadata['failed_provider'] = failed_provider
                response.metadata['error'] = error
                
                return response
                
            except Exception:
                continue
        
        # If all providers fail, raise error
        raise Exception(f"All providers failed. Original error from {failed_provider}: {error}")
    
    def _save_message(
        self,
        db: Session,
        conversation_id: str,
        role: str,
        content: str,
        provider: Optional[str],
        model: Optional[str],
        tokens_input: int,
        tokens_output: int
    ) -> Message:
        """Save a message to the database"""
        print(f"DEBUG _save_message: conv_id={conversation_id}, role={role}, provider={provider}")
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            provider=provider,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        print(f"DEBUG _save_message saved: id={message.id}, conv_id={message.conversation_id}")
        return message
    
    def _save_context_snapshot(
        self,
        db: Session,
        message_id: str,
        context_hash: str,
        context_package: ContextPackage,
        metadata: Dict[str, Any]
    ):
        """Save context snapshot for reproducibility"""
        ContextSnapshot.create_snapshot(
            db, message_id, context_hash,
            {
                "messages": context_package.messages,
                "temperature": context_package.temperature,
                "max_tokens": context_package.max_tokens
            },
            metadata
        )
    
    async def _embedding_worker(self):
        """
        Background worker to generate embeddings for messages
        """
        while True:
            try:
                # Get message from queue
                message_id, content = await self._embedding_queue.get()
                
                # Generate embedding
                embedding = await asyncio.to_thread(
                    self.embedding_model.encode, content
                )
                
                # Save to database
                # Note: This needs proper session handling in production
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    MessageEmbedding.create(
                        db, message_id, embedding.tolist(), self.embedding_model_name
                    )
                    print(f"Generated embedding for message {message_id}")
                except Exception as e:
                    print(f"Error saving embedding for message {message_id}: {e}")
                    db.rollback()
                finally:
                    db.close()
                    
            except Exception as e:
                print(f"Error in embedding worker: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying


# Singleton instance
context_orchestrator = ContextOrchestrator()