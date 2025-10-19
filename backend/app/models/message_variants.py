# backend/app/models/message_variants.py
"""
Message Variant model for tracking alternative AI responses
Allows users to compare and select between different model outputs
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship, Session
from app.database import Base


class MessageVariant(Base):
    """Message variant - alternative responses to the same user message"""
    __tablename__ = "message_variants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)  # The alternative response
    provider = Column(String(50), nullable=False)  # Provider used
    model = Column(String(100), nullable=False)  # Model used
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    is_canonical = Column(Boolean, default=False)  # True if this variant was selected as the main answer
    context_hash = Column(String(64))  # SHA256 hash of context used (links to context_snapshots)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to original message
    original_message = relationship("Message", foreign_keys=[original_message_id])
    
    @classmethod
    def create(
        cls,
        db: Session,
        original_message_id: str,
        content: str,
        provider: str,
        model: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        context_hash: Optional[str] = None,
        is_canonical: bool = False
    ):
        """Create a new message variant"""
        variant = cls(
            original_message_id=original_message_id,
            content=content,
            provider=provider,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            context_hash=context_hash,
            is_canonical=is_canonical
        )
        db.add(variant)
        db.commit()
        db.refresh(variant)
        return variant
    
    @classmethod
    def get_variants_for_message(
        cls,
        db: Session,
        original_message_id: str,
        limit: int = 2
    ) -> List['MessageVariant']:
        """Get variants for a specific message (max 2 alternatives)"""
        return db.query(cls).filter(
            cls.original_message_id == original_message_id
        ).order_by(cls.created_at).limit(limit).all()
    
    @classmethod
    def set_canonical(
        cls,
        db: Session,
        variant_id: str,
        original_message_id: str
    ):
        """
        Set a variant as canonical (selected by user)
        Updates the original message with this variant's content/provider/model
        Returns the updated original message
        """
        from app.models.chat import Message
        
        # Get the variant
        variant = db.query(cls).filter(cls.id == variant_id).first()
        if not variant:
            raise ValueError(f"Variant {variant_id} not found")
        
        # Get the original message - use direct filter without join
        original = db.query(Message).filter(
            Message.id == original_message_id
        ).first()
        
        if not original:
            raise ValueError(f"Original message {original_message_id} not found")
        
        # Update the original message with variant's content and metadata
        original.content = variant.content
        original.provider = variant.provider
        original.model = variant.model
        original.tokens_input = variant.tokens_input
        original.tokens_output = variant.tokens_output
        
        # Mark all variants of this message as non-canonical
        db.query(cls).filter(
            cls.original_message_id == original_message_id
        ).update({cls.is_canonical: False})
        
        # Mark this variant as canonical
        variant.is_canonical = True
        
        db.commit()
        db.refresh(original)
        
        return original
    
    @classmethod
    def get_by_id(cls, db: Session, variant_id: str):
        """Get variant by ID"""
        return db.query(cls).filter(cls.id == variant_id).first()
    
    def to_dict(self):
        """Convert variant to dictionary"""
        return {
            "id": self.id,
            "original_message_id": self.original_message_id,
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "is_canonical": self.is_canonical,
            "context_hash": self.context_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }