from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from infra.configuration import DatabaseSettings


def create_db_engine(
    settings: DatabaseSettings,
) -> Engine:
    """Create a SQLAlchemy Engine from database settings.
    
    Args:
        settings: Database settings containing the connection URL.
    
    Returns:
        A configured SQLAlchemy Engine (does not connect until used).
    """
    return create_engine(settings.url.get_secret_value())
