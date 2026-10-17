"""SQLAlchemy engine, session factory, and base model."""
from datetime import datetime, timezone

from sqlalchemy import create_engine, event, String
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import TypeDecorator

from ..core.config import settings

engine: Engine = create_engine(settings.database_url, echo=False, future=True)  # type: ignore[arg-type]
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


class UTCDateTime(TypeDecorator):
    """Store datetimes as ISO-8601 strings in UTC, always timezone-aware.

    SQLite lacks native datetime support and stores values as text.
    This decorator ensures round-tripping preserves timezone information.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

    def process_result_value(self, value: str | None, dialect) -> datetime | None:
        if value is None:
            return None
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    """Enforce foreign keys on SQLite connections."""
    dbapi_conn.execute("PRAGMA foreign_keys=ON")


def get_db():
    """FastAPI dependency: yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)