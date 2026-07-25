import os

from sqlalchemy import text
from sqlalchemy.engine import Engine, make_url

from infra.persistence.database_engine import create_db_engine
from infra.persistence.database_settings import DatabaseSettings


def create_test_engine() -> Engine:
    database_url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("TEST_DATABASE_URL must be defined")

    url = make_url(database_url)
    if url.drivername != "postgresql+psycopg":
        raise RuntimeError("TEST_DATABASE_URL must use postgresql+psycopg")
    if url.host not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("TEST_DATABASE_URL must use a loopback host")
    if url.port != 54322 or url.database != "postgres":
        raise RuntimeError(
            "TEST_DATABASE_URL must target local port 54322/database postgres"
        )

    return create_db_engine(DatabaseSettings(database_url))


def clean_warehouse_tables(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE public.raw_material_bales, "
                "public.raw_material_batches"
            )
        )
