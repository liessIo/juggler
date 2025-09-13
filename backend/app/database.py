# backend/app/database.py

"""
Simplified database setup for Juggler
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create database directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Database URL - construct from DATABASE_PATH
DATABASE_URL = f"sqlite:///{settings.DATABASE_PATH}/juggler.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base - this is what models will inherit from
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database with tables"""
    # Import models here to avoid circular imports
    # This ensures models are registered with Base before creating tables
    from app.models import security_models
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DATABASE_URL}")
    
    # Create test user only in DEBUG mode
    if settings.DEBUG:
        from sqlalchemy.orm import Session
        from app.models.auth_utils import get_password_hash
        from app.models.security_models import User
        import uuid
        
        db = SessionLocal()
        try:
            # Check if test user exists
            existing_user = db.query(User).filter(User.username == "testuser").first()
            
            if not existing_user:
                # Create test user
                test_user = User(
                    id=str(uuid.uuid4()),
                    username="testuser",
                    email="test@example.com",
                    hashed_password=get_password_hash("Test123!"),
                    is_active=True,
                    is_superuser=False
                )
                db.add(test_user)
                db.commit()
                print("Test user created (username: testuser, password: Test123!)")
            else:
                print("Test user already exists")
                
        except Exception as e:
            print(f"Error creating test user: {e}")
            db.rollback()
        finally:
            db.close()

if __name__ == "__main__":
    init_db()