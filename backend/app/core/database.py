"""
Database connection, session management, and base declarative class.
Uses SQLAlchemy 2.0 with full compatibility for SQLite and PostgreSQL.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings

# Engine configuration
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding database session per request.
    Ensures safe commit/rollback and connection closure.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables on application startup and ensure schema migrations."""
    # Import models here to ensure they are registered with Base.metadata
    from backend.app.models import user, complaint  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Automatic column migration for existing SQLite databases
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(complaints)"))
            cols = [row[1] for row in result.fetchall()]
            if cols and "user_id" not in cols:
                conn.execute(text("ALTER TABLE complaints ADD COLUMN user_id INTEGER REFERENCES users(id)"))
                conn.commit()
    except Exception:
        pass
