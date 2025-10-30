"""
Database Configuration and Connection Management

Handles PostgreSQL connection pooling, session management, and pgvector setup.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from mcp_bets.config.settings import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base for ORM models
Base = declarative_base()

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using them
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ============================================================================
# pgvector Extension Setup
# ============================================================================

def enable_pgvector_extension():
    """
    Enable pgvector extension for vector similarity search
    
    This must be run after database creation and before creating tables.
    """
    try:
        with engine.connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            conn.commit()
            logger.info("✅ PostgreSQL extensions enabled (vector, uuid-ossp)")
    except Exception as e:
        logger.error(f"❌ Failed to enable PostgreSQL extensions: {e}")
        raise


# ============================================================================
# Database Session Management
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session
    
    Usage in FastAPI route:
        @app.get("/")
        def read_root(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions outside FastAPI routes
    
    Usage:
        with get_db_context() as db:
            result = db.query(Player).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Database Initialization
# ============================================================================

def init_database():
    """
    Initialize database: create extensions and tables
    
    Call this once on application startup.
    """
    logger.info("Initializing database...")
    
    # Enable extensions first
    enable_pgvector_extension()
    
    # Import all models so they're registered with Base
    from mcp_bets import models  # noqa: F401
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized successfully")


def drop_all_tables():
    """
    Drop all tables (use with caution!)
    
    Only use in development/testing.
    """
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Cannot drop tables in production environment!")
    
    logger.warning("⚠️  Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("✅ All tables dropped")


# ============================================================================
# Database Health Check
# ============================================================================

def check_database_health() -> bool:
    """
    Check if database is accessible and healthy
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✅ Database health check passed")
        return True
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return False
