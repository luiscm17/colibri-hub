import unittest
from types import TracebackType
from typing import Self, cast
from unittest.mock import patch

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from bootstrap.database_session_dependency import session_dependency
from infra.configuration import DatabaseSettings
from infra.persistence.database_engine import create_db_engine


class RecordingSession:
    """Context-manager session double that records exit exception types."""

    def __init__(self) -> None:
        self.exit_types: list[type[BaseException] | None] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exception, traceback
        self.exit_types.append(exception_type)


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
        """The session_dependency generator creates a new session per invocation and exits it on normal completion or exception."""
        factory = RecordingSessionFactory()
        provider = session_dependency(factory)

        normal = provider()
        self.assertIs(next(normal), factory.sessions[0])
        with self.assertRaises(StopIteration):
            next(normal)

        exceptional = provider()
        next(exceptional)
        with self.assertRaises(RuntimeError):
            exceptional.throw(RuntimeError("request failure"))

        self.assertEqual(len(factory.sessions), 2)
        self.assertEqual(factory.sessions[0].exit_types, [None])
        self.assertEqual(factory.sessions[1].exit_types, [RuntimeError])
