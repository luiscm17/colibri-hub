import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url


def validated_test_database_url() -> str:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if database_url is None:
        raise RuntimeError("TEST_DATABASE_URL must name the guarded local PostgreSQL database.")

    url = make_url(database_url)
    if (
        url.drivername != "postgresql+psycopg"
        or url.host not in {"127.0.0.1", "localhost", "::1"}
        or url.port != 54322
        or url.database != "postgres"
    ):
        raise RuntimeError("TEST_DATABASE_URL must name the guarded local PostgreSQL database.")
    return database_url


def test_engine() -> Engine:
    return create_engine(validated_test_database_url())


def cleanup_slice_five_rows(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "DELETE FROM raw_material_bales "
                "WHERE raw_material_batch_id IN ("
                "SELECT id FROM raw_material_batches WHERE provider_name = 'slice5-test')"
            )
        )
        connection.execute(
            text("DELETE FROM raw_material_batches WHERE provider_name = 'slice5-test'")
        )


def cleanup_slice_six_rows(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "DELETE FROM raw_material_bales WHERE raw_material_batch_id IN ("
                "SELECT id FROM raw_material_batches WHERE provider_name = 'slice6-test')"
            )
        )
        connection.execute(
            text("DELETE FROM raw_material_batches WHERE provider_name = 'slice6-test'")
        )
