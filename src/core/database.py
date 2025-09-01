"""
Database Configuration and Setup for NHS Paperwork Automation Agent
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from ..models.database import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for NHS Paperwork Agent"""
    
    def __init__(self, database_url: str = None):
        """Initialize database manager"""
        
        # Use provided URL or get from environment
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", 
            "sqlite:///./data/nhs_agent.db"
        )
        
        # Create engine based on database type
        if self.database_url.startswith("sqlite"):
            # SQLite configuration for development
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=os.getenv("DEBUG", "False").lower() == "true"
            )
        else:
            # PostgreSQL configuration for production
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                echo=os.getenv("DEBUG", "False").lower() == "true"
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Ensure data directory exists for SQLite
        if self.database_url.startswith("sqlite"):
            db_path = self.database_url.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise e
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    @contextmanager
    def get_session_context(self):
        """Get a database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise e
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check if database is accessible"""
        try:
            with self.get_session_context() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False


# Global database manager instance
db_manager: DatabaseManager = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
        db_manager.create_tables()
    return db_manager


def get_db_session():
    """Dependency for getting database session in FastAPI"""
    db = get_database_manager()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()
