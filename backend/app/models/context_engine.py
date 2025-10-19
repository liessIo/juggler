# backend/app/models/context_engine.py
"""
Context Engine models for Juggler v3
Requires PostgreSQL with pgvector extension
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.database import Base


class MessageEmbedding(Base):
    """Vector embeddings for semantic message search"""
    __tablename__ = "message_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    embedding = Column(Vector(384))  # all-MiniLM-L6-v2 dimension
    model = Column(String(100), default="all-MiniLM-L6-v2")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    message = relationship("Message")
    
    @classmethod
    def create(cls, db: Session, message_id: str, embedding: List[float], model: str = "all-MiniLM-L6-v2"):
        """Create a new embedding"""
        embedding_obj = cls(
            message_id=message_id,
            embedding=embedding,
            model=model
        )
        db.add(embedding_obj)
        db.commit()
        db.refresh(embedding_obj)
        return embedding_obj
    
    @classmethod
    def search_similar(
        cls, 
        db: Session, 
        query_embedding: List[float], 
        conversation_id: Optional[str] = None,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[tuple]:
        """
        Search for similar messages using cosine similarity
        Returns list of (message, similarity_score) tuples
        """
        from app.models.chat import Message
        
        query = db.query(Message, cls.embedding.cosine_distance(query_embedding).label("distance"))\
            .join(cls, Message.id == cls.message_id)
        
        if conversation_id:
            query = query.filter(Message.conversation_id == conversation_id)
        
        # Convert distance to similarity (1 - distance)
        results = query.order_by("distance").limit(limit).all()
        
        similar_messages = []
        for msg, distance in results:
            similarity = 1 - distance
            if similarity >= threshold:
                similar_messages.append((msg, similarity))
        
        return similar_messages


class RetrievalLog(Base):
    """Logs of retrieved messages for transparency"""
    __tablename__ = "retrieval_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    turn_id = Column(Integer, nullable=False)  # Which turn in the conversation
    retrieved_message_id = Column(String(36), ForeignKey("messages.id"))
    score = Column(Float, nullable=False)
    reason = Column(Text)  # Why this message was retrieved
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation")
    retrieved_message = relationship("Message")
    
    @classmethod
    def log_retrieval(
        cls,
        db: Session,
        conversation_id: str,
        turn_id: int,
        retrieved_message_id: str,
        score: float,
        reason: str
    ):
        """Log a message retrieval"""
        log = cls(
            conversation_id=conversation_id,
            turn_id=turn_id,
            retrieved_message_id=retrieved_message_id,
            score=score,
            reason=reason
        )
        db.add(log)
        db.commit()
        return log


class ContextSnapshot(Base):
    """Snapshots of context used for each message generation"""
    __tablename__ = "context_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generating_message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    context_hash = Column(String(64), nullable=False)  # SHA256 hash
    snapshot_data = Column(JSONB, nullable=False)  # Complete context package
    snapshot_metadata = Column("metadata", JSONB)  # Map to DB column 'metadata' but use snapshot_metadata in code
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    message = relationship("Message")
    
    @classmethod
    def create_snapshot(
        cls,
        db: Session,
        message_id: str,
        context_hash: str,
        snapshot_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Create a context snapshot"""
        snapshot = cls(
            generating_message_id=message_id,
            context_hash=context_hash,
            snapshot_data=snapshot_data,
            snapshot_metadata=metadata
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot
    
    @classmethod
    def get_by_message_id(cls, db: Session, message_id: str):
        """Get snapshot for a specific message"""
        return db.query(cls).filter(cls.generating_message_id == message_id).first()
    
    @classmethod
    def get_by_hash(cls, db: Session, context_hash: str):
        """Get snapshots with a specific context hash"""
        return db.query(cls).filter(cls.context_hash == context_hash).all()


class ProviderHealth(Base):
    """Health status of AI providers for circuit breaker"""
    __tablename__ = "provider_health"
    
    provider = Column(String(50), primary_key=True)
    status = Column(String(20), default="healthy")  # healthy, degraded, down
    failure_count = Column(Integer, default=0)
    last_failure_at = Column(DateTime)
    opened_until = Column(DateTime)  # Circuit breaker open until this time
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_status(cls, db: Session, provider: str) -> 'ProviderHealth':
        """Get or create provider health status"""
        health = db.query(cls).filter(cls.provider == provider).first()
        if not health:
            health = cls(provider=provider)
            db.add(health)
            db.commit()
            db.refresh(health)
        return health
    
    @classmethod
    def record_success(cls, db: Session, provider: str):
        """Record a successful call"""
        health = cls.get_status(db, provider)
        health.failure_count = 0
        health.status = "healthy"
        health.opened_until = None
        health.updated_at = datetime.utcnow()
        db.commit()
    
    @classmethod
    def record_failure(cls, db: Session, provider: str, threshold: int = 5, timeout_seconds: int = 60):
        """Record a failed call and potentially open circuit"""
        from datetime import timedelta
        
        health = cls.get_status(db, provider)
        health.failure_count += 1
        health.last_failure_at = datetime.utcnow()
        
        if health.failure_count >= threshold:
            health.status = "down"
            health.opened_until = datetime.utcnow() + timedelta(seconds=timeout_seconds)
        elif health.failure_count >= threshold // 2:
            health.status = "degraded"
        
        health.updated_at = datetime.utcnow()
        db.commit()
        return health
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        if self.status == "healthy":
            return True
        
        if self.status == "down" and self.opened_until:
            # Check if circuit breaker timeout has passed
            if datetime.utcnow() > self.opened_until:
                self.status = "degraded"  # Allow retry
                self.failure_count = self.failure_count // 2  # Reduce failure count
                return True
            return False
        
        return self.status == "degraded"  # Allow degraded providers with caution


# Update existing Message and Conversation models to include new relationships
def update_existing_models():
    """
    This function should be called to add relationships to existing models
    Import and update in the main chat.py file
    """
    from app.models.chat import Message, Conversation
    
    # Add relationships if they don't exist
    if not hasattr(Message, 'embeddings'):
        Message.embeddings = relationship("MessageEmbedding", cascade="all, delete-orphan")
    
    if not hasattr(Message, 'context_snapshot'):
        Message.context_snapshot = relationship("ContextSnapshot", uselist=False)
    
    if not hasattr(Conversation, 'retrieval_logs'):
        Conversation.retrieval_logs = relationship("RetrievalLog", cascade="all, delete-orphan")