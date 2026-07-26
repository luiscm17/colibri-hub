from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def create_session_factory(
    engine: Engine,
) -> sessionmaker[Session]:
    """Create a session factory bound to the given database engine.
    
    Args:
        engine: A configured SQLAlchemy Engine.
    
    Returns:
        A sessionmaker that creates new ORM sessions.
    """
    return sessionmaker(bind=engine)
