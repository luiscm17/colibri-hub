import unittest
from typing import cast
from unittest.mock import patch

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from bootstrap.database_session_dependency import session_dependency
from infra.configuration import DatabaseSettings
from infra.persistence.database_engine import create_db_engine


class RecordingSession:
    """Session double that records commit/rollback/close lifecycle calls."""

    def __init__(self) -> None:
        self.committed: bool = False
        self.rolled_back: bool = False
        self.closed: bool = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


class RecordingSessionFactory:
    """Callable factory double that records every session it creates."""

    def __init__(self) -> None:
        self.sessions: list[RecordingSession] = []

    def __call__(self) -> Session:
        session = RecordingSession()
        self.sessions.append(session)
        return cast(Session, session)


class DatabaseResourceTests(unittest.TestCase):
    """Database resource contracts: engine creation, URL unwrapping, and session lifecycle."""

    def test_engine_unwraps_secret_at_creation_seam_without_connecting(self) -> None:
        """create_db_engine constructs an engine with the unwrapped URL without establishing a connection."""
        connections: list[object] = []

        def record_connection(
            database_connection: object, connection_record: object
        ) -> None:
            del database_connection
            connections.append(connection_record)

        event.listen(Engine, "connect", record_connection)
        engine = create_db_engine(DatabaseSettings(url="sqlite+pysqlite:///:memory:"))
        try:
            self.assertEqual(str(engine.url), "sqlite+pysqlite:///:memory:")
            self.assertEqual(connections, [])
        finally:
            engine.dispose()
            event.remove(Engine, "connect", record_connection)

    def test_engine_factory_receives_only_the_unwrapped_database_url(self) -> None:
        """The engine factory callable is invoked with the unwrapped secret value, not the SecretStr."""
        settings = DatabaseSettings(url="postgresql+psycopg://user:secret@host/database")
        with patch("infra.persistence.database_engine.create_engine") as create_engine:
            create_db_engine(settings)
        create_engine.assert_called_once_with(settings.url.get_secret_value())

    def test_session_dependency_creates_and_closes_one_session_per_invocation(self) -> None:
        """The session_dependency generator commits on success, rolls back on exception, and always closes."""
        factory = RecordingSessionFactory()
        provider = session_dependency(factory)

        normal = provider()
        session = next(normal)
        self.assertIs(session, factory.sessions[0])
        with self.assertRaises(StopIteration):
            next(normal)
        self.assertTrue(factory.sessions[0].committed)
        self.assertFalse(factory.sessions[0].rolled_back)
        self.assertTrue(factory.sessions[0].closed)

        exceptional = provider()
        next(exceptional)
        with self.assertRaises(RuntimeError):
            exceptional.throw(RuntimeError("request failure"))
        self.assertFalse(factory.sessions[1].committed)
        self.assertTrue(factory.sessions[1].rolled_back)
        self.assertTrue(factory.sessions[1].closed)

        self.assertEqual(len(factory.sessions), 2)
