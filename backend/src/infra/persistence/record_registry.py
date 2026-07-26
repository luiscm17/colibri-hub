from sqlalchemy.orm import DeclarativeBase


class RecordRegistry(DeclarativeBase):
    """Base class for all SQLAlchemy ORM records in the system.
    
    All mapped ORM classes should inherit from this registry to share
    the same DeclarativeBase metadata.
    """