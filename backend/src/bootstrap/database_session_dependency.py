from collections.abc import Callable, Generator

from sqlalchemy.orm import Session

SessionFactory = Callable[[], Session]
"""Type alias for a factory that creates new SQLAlchemy sessions."""

SessionProvider = Callable[[], Generator[Session, None, None]]
"""Type alias for a FastAPI-compatible session dependency."""


def session_dependency(
    session_factory: SessionFactory,
) -> SessionProvider:
    """Build a FastAPI dependency that yields a session per request.
    
    Creates a new session from the factory for each request and
    ensures it is closed when the request completes.
    
    Args:
        session_factory: A callable that returns a new SQLAlchemy Session.
    
    Returns:
        A generator-based dependency for use with FastAPI Depends.
    """
    def database_session() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    return database_session
