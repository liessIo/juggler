# backend/app/database.py

"""
Database setup and session management for Juggler
Using SQLite for simplicity - can be migrated to PostgreSQL later
"""

from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import uuid
from pathlib import Path
from contextlib import contextmanager
from passlib.context import CryptContext

# Create database directory
DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)

# Database URL - SQLite for development
DATABASE_URL = f"sqlite:///{DB_DIR}/juggler.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============== Models ==============

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(username='{self.username}')>"

class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Conversation(id='{self.id}', user_id='{self.user_id}')>"

class Message(Base):
    """Message model"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, nullable=False)
    
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    
    token_count = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Message(role='{self.role}', conversation_id='{self.conversation_id}')>"

# ============== Database Functions ==============

def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DATABASE_URL}")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ============== User Functions ==============

def create_user(username: str, email: str, password: str) -> dict:
    """Create a new user"""
    with get_db_context() as db:
        # Check if user exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing:
            raise ValueError("User already exists")
        
        # Create new user
        user = User(
            username=username,
            email=email,
            hashed_password=pwd_context.hash(password)
        )
        db.add(user)
        db.commit()
        
        # Return user data as dict (not the object)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }

def get_user_by_username(username: str) -> User:
    """Get user by username"""
    with get_db_context() as db:
        return db.query(User).filter(User.username == username).first()

def verify_user_password(username: str, password: str):
    """Verify user password and return user if valid"""
    with get_db_context() as db:
        user = db.query(User).filter(User.username == username).first()
        if user and pwd_context.verify(password, user.hashed_password):
            # Update last login
            db.query(User).filter(User.id == user.id).update(
                {"last_login": datetime.utcnow()}
            )
            db.commit()
            
            # Return user data within session context
            return User(
                id=user.id,
                username=user.username,
                email=user.email,
                hashed_password=user.hashed_password
            )
    return None

def list_users():
    """List all users (for debugging)"""
    with get_db_context() as db:
        users = db.query(User).all()
        for user in users:
            print(f"User: {user.username} ({user.email})")

# ============== Conversation Functions ==============

def create_conversation(user_id: str, title: str = None) -> Conversation:
    """Create a new conversation"""
    with get_db_context() as db:
        conv = Conversation(user_id=user_id, title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

def get_user_conversations(user_id: str):
    """Get all conversations for a user"""
    with get_db_context() as db:
        return db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.created_at.desc()).all()

# ============== Message Functions ==============

def add_message(
    conversation_id: str,
    role: str,
    content: str,
    provider: str = None,
    model: str = None
) -> Message:
    """Add a message to a conversation"""
    with get_db_context() as db:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            provider=provider,
            model=model
        )
        db.add(msg)
        
        # Update conversation updated_at
        db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).update({"updated_at": datetime.utcnow()})
        
        db.commit()
        db.refresh(msg)
        return msg

def get_conversation_messages(conversation_id: str):
    """Get all messages in a conversation"""
    with get_db_context() as db:
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

# ============== Setup Script ==============

def setup_database_with_test_user():
    """Initialize database and create test user"""
    print("Setting up database...")
    init_db()
    
    try:
        # Create test user
        user_data = create_user(
            username="testuser",
            email="test@test.com",
            password="Test123!"
        )
        print(f"✅ Created test user: testuser")
        
        # Create another test user
        user_data2 = create_user(
            username="demo",
            email="demo@test.com", 
            password="Demo123!"
        )
        print(f"✅ Created demo user: demo")
        
    except ValueError as e:
        print(f"ℹ️ Users might already exist: {e}")
    
    print("\n✅ Database setup complete!")
    print("You can now login with:")
    print("  Username: testuser / Password: Test123!")
    print("  Username: demo / Password: Demo123!")

if __name__ == "__main__":
    # Run this script directly to setup database
    setup_database_with_test_user()