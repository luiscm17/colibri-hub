from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from infra.configuration import DatabaseSettings


def create_db_engine(
    settings: DatabaseSettings,
) -> Engine:
    return create_engine(settings.url.get_secret_value())
