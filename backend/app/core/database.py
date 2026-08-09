from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for the auth persistence models."""


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Lazily create the shared SQLAlchemy engine (process-wide singleton)."""
    global _engine, _session_factory
    if _engine is None:
        url = settings.resolved_database_url
        _engine = create_engine(url, **(_engine_kwargs(url)))
        _session_factory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    assert _session_factory is not None
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


def init_db() -> None:
    """Create all tables. Idempotent; safe to call on every app start."""
    import app.models  # noqa: F401  (register ORM models on Base before create_all)

    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session]:
    """FastAPI dependency yielding a scoped SQLAlchemy session."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
