# backend/app/database.py

"""
Database setup and session management for Juggler
Using SQLite for simplicity - can be migrated to PostgreSQL later
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import uuid
from pathlib import Path
from contextlib import contextmanager
from passlib.context import CryptContext

# Import models from security_models - handle both package and direct execution
try:
    # When run as part of package
    from app.models.security_models import Base, User, Conversation, APIKey
    from app.security.key_manager import initialize_key_manager
except ImportError:
    # When run directly
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.security_models import Base, User, Conversation, APIKey
    from security.key_manager import initialize_key_manager

# Create database directory
DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)

# Database URL - SQLite for development
DATABASE_URL = f"sqlite:///{DB_DIR}/juggler.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

def create_user(username: str, email: str, password: str, full_name: str = "") -> dict:
    """Create a new user - supports full_name parameter"""
    with get_db_context() as db:
        # Check if user exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing:
            raise ValueError("User already exists")
        
        # Create new user with all required fields
        user = User(
            username=username,
            email=email,
            hashed_password=pwd_context.hash(password),
            full_name=full_name,
            is_active=True,
            is_verified=False,  # Set default value
            is_admin=False      # Set default value
        )
        db.add(user)
        db.commit()
        
        # Return user data as dict (not the object)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }

def get_user_by_username(username: str) -> User:
    """Get user by username"""
    with get_db_context() as db:
        return db.query(User).filter(User.username == username).first()

def verify_user_password(username: str, password: str):
    """Verify user password and return user if valid"""
    with get_db_context() as db:
        user = db.query(User).filter(User.username == username).first()
        if user and pwd_context.verify(password, str(user.hashed_password)):
            # Update last login
            db.query(User).filter(User.id == user.id).update(
                {"last_login": datetime.utcnow()}
            )
            db.commit()
            
            # Return user data within session context
            class UserData:
                def __init__(self, id, username, email, hashed_password, full_name=None):
                    self.id = id
                    self.username = username
                    self.email = email
                    self.hashed_password = hashed_password
                    self.full_name = full_name
            
            return UserData(
                id=str(user.id),
                username=str(user.username),
                email=str(user.email),
                hashed_password=str(user.hashed_password),
                full_name=getattr(user, 'full_name', None)
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

class Message:
    """Simple Message class for backward compatibility"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

def add_message(
    conversation_id: str,
    role: str,
    content: str,
    provider: str = "default",
    model: str = "default"
) -> Message:
    """Add a message to a conversation - simplified for backward compatibility"""
    # For now, just return a simple message object
    # In a full implementation, you'd want a proper Message model
    msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
        provider=provider,
        model=model,
        created_at=datetime.utcnow()
    )
    
    # Update conversation updated_at
    with get_db_context() as db:
        db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).update({"updated_at": datetime.utcnow()})
        db.commit()
    
    return msg

def get_conversation_messages(conversation_id: str):
    """Get all messages in a conversation - simplified"""
    # For backward compatibility, return empty list
    # In full implementation, query actual Message model
    return []

# ============== Setup Script ==============

def setup_database_with_test_user():
    """Initialize database and create test user"""
    print("Setting up database...")
    
    # Initialize key manager first
    from app.config import settings
    initialize_key_manager(settings.SECRET_KEY)
    
    init_db()
    
    # Only create test users in development mode
    if settings.DEBUG:
        print("DEBUG mode detected - creating test users...")
        try:
            # Create test user
            user_data = create_user(
                username="testuser",
                email="test@test.com",
                password="Test123!",
                full_name="Test User"
            )
            print(f"Created test user: testuser")
            
            # Create another test user
            user_data2 = create_user(
                username="demo",
                email="demo@test.com", 
                password="Demo123!",
                full_name="Demo User"
            )
            print(f"Created demo user: demo")
            
            print("\nTest users created for development:")
            print("  Username: testuser / Password: Test123!")
            print("  Username: demo / Password: Demo123!")
            
        except ValueError as e:
            print(f"Test users might already exist: {e}")
    else:
        print("Production mode - no test users created")
        print("Create users through the registration API endpoints")
    
    print("\nDatabase setup complete!")

if __name__ == "__main__":
    # Run this script directly to setup database
    setup_database_with_test_user()