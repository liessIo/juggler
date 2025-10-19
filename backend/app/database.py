# File: backend/app/database.py
"""
Database configuration for Juggler v3 with PostgreSQL + pgvector support
"""

from dotenv import load_dotenv
load_dotenv()

import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/juggler.db")

# Determine if we're using PostgreSQL or SQLite
is_postgres = DATABASE_URL.startswith("postgresql")

if is_postgres:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,         # Number of connections to maintain
        max_overflow=10,     # Maximum overflow connections
        echo=False           # Set to True for SQL debugging
    )
    
    # Create pgvector extension if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
else:
    # SQLite configuration (fallback for development)
    if DATABASE_URL.startswith("sqlite"):
        # For SQLite, we need to handle some special cases
        connect_args = {"check_same_thread": False}
        poolclass = StaticPool
    else:
        connect_args = {}
        poolclass = None
    
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        poolclass=poolclass,
        echo=False
    )
    
    # Enable foreign keys for SQLite
    if DATABASE_URL.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - create all tables"""
    # Import all models to ensure they're registered
    from app.models import user, chat, system_config, model_selection
    
    # Only import Context Engine models if using PostgreSQL
    if is_postgres:
        try:
            from app.models import context_engine
        except ImportError:
            print("Warning: Context Engine models not available")
    
    Base.metadata.create_all(bind=engine)

def get_database_info():
    """Get information about the current database"""
    info = {
        "type": "PostgreSQL" if is_postgres else "SQLite",
        "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
        "pgvector": False
    }
    
    if is_postgres:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            info["pgvector"] = result.fetchone() is not None
    
    return info