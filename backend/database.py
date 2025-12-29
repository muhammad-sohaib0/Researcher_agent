# Database Configuration

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from typing import Generator

# Import config for database URL
from core.config import get_settings

# Database URL from settings
settings = get_settings()
SQLALCHEMY_DATABASE_URL = settings.database_url

# Create engine with proper configuration
if SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600
    )
else:
    # SQLite configuration (default)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for DB session (for use outside FastAPI)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all database tables (use with caution)."""
    Base.metadata.drop_all(bind=engine)


# SQLite foreign key constraint enable
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance and foreign key support."""
    if "sqlite" in str(type(dbapi_connection)):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


class DatabaseManager:
    """Database manager for advanced operations."""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal

    def get_session(self) -> Session:
        """Get a new database session."""
        return SessionLocal()

    def execute_raw_sql(self, sql: str, params: dict = None):
        """Execute raw SQL query."""
        with self.engine.connect() as conn:
            result = conn.execute(sql, params or {})
            conn.commit()
            return result

    def bulk_insert(self, model, records: list):
        """Bulk insert records."""
        with self.engine.begin() as conn:
            conn.execute(model.__table__.insert(), records)

    def check_connection(self) -> bool:
        """Check if database connection is healthy."""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def get_table_names(self) -> list:
        """Get list of all table names."""
        return [table.name for table in Base.metadata.sorted_tables]

    def vacuum(self) -> None:
        """Vacuum the database (SQLite only)."""
        if "sqlite" in str(self.engine.url):
            with self.engine.connect() as conn:
                conn.execute("VACUUM")


# Global database manager instance
db_manager = DatabaseManager()
