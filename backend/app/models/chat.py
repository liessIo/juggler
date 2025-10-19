"""
Chat models for conversations and messages
Updated with Context Engine relationships
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship, Session
from app.database import Base


class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_tokens = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    # Context Engine relationships (only if PostgreSQL)
    #retrieval_logs = relationship("RetrievalLog", back_populates="conversation", cascade="all, delete-orphan")
    
    @classmethod
    def create(cls, db: Session, user_id: str, title: Optional[str] = None):
        """Create a new conversation"""
        conversation = cls(
            user_id=user_id,
            title=title or f"New Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    @classmethod
    def get_by_id(cls, db: Session, conversation_id: str, user_id: str):
        """Get conversation by ID and user"""
        return db.query(cls).filter(
            cls.id == conversation_id,
            cls.user_id == user_id
        ).first()
    
    @classmethod
    def list_by_user(cls, db: Session, user_id: str, limit: int = 50):
        """List conversations for a user"""
        return db.query(cls).filter(
            cls.user_id == user_id
        ).order_by(cls.updated_at.desc()).limit(limit).all()
    
    def update_title(self, db: Session, title: str):
        """Update conversation title"""
        self.title = title
        self.updated_at = datetime.utcnow()
        db.commit()
        return self
    
    def update_tokens(self, db: Session, tokens: int):
        """Update total tokens used"""
        self.total_tokens += tokens
        self.updated_at = datetime.utcnow()
        db.commit()


class Message(Base):
    """Message model"""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    provider = Column(String(50))  # Which provider was used
    model = Column(String(100))  # Which model was used
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON)  # Additional metadata
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Context Engine relationships (only if PostgreSQL)
    #embeddings = relationship("MessageEmbedding", back_populates="message", cascade="all, delete-orphan")
    #context_snapshot = relationship("ContextSnapshot", back_populates="message", uselist=False)
    
    @classmethod
    def create(
        cls,
        db: Session,
        conversation_id: str,
        role: str,
        content: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        metadata: Optional[dict] = None
    ):
        """Create a new message"""
        message = cls(
            conversation_id=conversation_id,
            role=role,
            content=content,
            provider=provider,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            timestamp=datetime.utcnow(),
            meta_data=metadata
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Update conversation timestamp and tokens
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
            conversation.total_tokens += tokens_input + tokens_output
            db.commit()
        
        return message
    
    @classmethod
    def get_by_conversation(cls, db: Session, conversation_id: str, limit: Optional[int] = None):
        """Get messages for a conversation"""
        query = db.query(cls).filter(
            cls.conversation_id == conversation_id
        ).order_by(cls.timestamp)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_recent(cls, db: Session, conversation_id: str, limit: int = 10):
        """Get recent messages from a conversation"""
        return db.query(cls).filter(
            cls.conversation_id == conversation_id
        ).order_by(cls.timestamp.desc()).limit(limit).all()[::-1]
    
    @classmethod
    def search_in_conversation(cls, db: Session, conversation_id: str, search_term: str):
        """Search for messages containing a term"""
        return db.query(cls).filter(
            cls.conversation_id == conversation_id,
            cls.content.contains(search_term)
        ).order_by(cls.timestamp).all()
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.meta_data
        }


# Import Context Engine models only if using PostgreSQL
def setup_context_engine_relationships():
    """Setup relationships with Context Engine models if available"""
    from app.settings import settings
    
    if settings.is_postgres() and settings.ENABLE_CONTEXT_ENGINE:
        try:
            from app.models.context_engine import update_existing_models
            update_existing_models()
            return True
        except ImportError:
            print("Warning: Context Engine models not available")
            return False
    return False