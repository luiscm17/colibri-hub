from sqlalchemy.orm import DeclarativeBase


class RecordRegistry(DeclarativeBase):
    """Base class for all SQLAlchemy ORM records in the system.
    
    All mapped ORM classes should inherit from this registry to share
    the same DeclarativeBase metadata.
    """


def register_access_records() -> None:
    """Load Access mappings into the shared SQLAlchemy metadata registry."""

    from access.adapters.persistence import records  # noqa: F401


def register_auth_records() -> None:
    """Load Authentication mappings into the shared SQLAlchemy metadata registry."""

    from auth.adapters.persistence import records  # noqa: F401
