import unittest
from unittest.mock import patch

from sqlalchemy import create_engine

from infra.configuration import DatabaseSettings
from infra.persistence.database_engine import create_db_engine
from infra.persistence.database_session_factory import create_session_factory


class TestDatabaseEngine(unittest.TestCase):
    def test_creates_engine_with_supplied_database_url_without_connecting(self) -> None:
        settings = DatabaseSettings(
            url="postgresql+psycopg://fixture_user:fixture_password@database.invalid/fixture_database"
        )
        expected_engine = object()

        with patch(
            "infra.persistence.database_engine.create_engine",
            return_value=expected_engine,
        ) as create_engine_mock:
            engine = create_db_engine(settings)

        self.assertIs(engine, expected_engine)
        create_engine_mock.assert_called_once_with(
            "postgresql+psycopg://fixture_user:fixture_password@database.invalid/fixture_database"
        )


class TestDatabaseSessionFactory(unittest.TestCase):
    def test_creates_sessions_bound_to_supplied_engine(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:")
        session = None

        try:
            session_factory = create_session_factory(engine)
            session = session_factory()

            self.assertIs(session.get_bind(), engine)
        finally:
            if session is not None:
                session.close()
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
