import unittest
from typing import Generator

from sqlalchemy.orm import Session

from bootstrap.database_session_dependency import (
    SessionProvider,
    session_dependency,
)


class FakeSession(Session):
    """Session subclass that tracks open/close."""

    def __init__(self) -> None:
        super().__init__()
        self.closed = False

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *args: object) -> None:
        self.closed = True


class FakeSessionFactory:
    def __init__(self) -> None:
        self.calls: list[FakeSession] = []

    def __call__(self) -> FakeSession:
        session = FakeSession()
        self.calls.append(session)
        return session


class TestSessionDependency(unittest.TestCase):
    def test_yields_session_from_factory(self) -> None:
        factory = FakeSessionFactory()
        provider = session_dependency(factory)

        generator = provider()
        session = next(generator)

        self.assertIsInstance(session, Session)
        self.assertIs(session, factory.calls[0])

    def test_closes_session_after_generator_exit(self) -> None:
        factory = FakeSessionFactory()
        provider = session_dependency(factory)

        generator = provider()
        session = next(generator)
        generator.close()

        self.assertTrue(session.closed)

    def test_creates_independent_sessions_per_call(self) -> None:
        factory = FakeSessionFactory()
        provider = session_dependency(factory)

        gen1 = provider()
        gen2 = provider()
        session1 = next(gen1)
        session2 = next(gen2)

        self.assertIsNot(session1, session2)

    def test_closes_session_on_exception_in_context(self) -> None:
        factory = FakeSessionFactory()
        provider = session_dependency(factory)

        generator = provider()
        session = next(generator)

        class TestException(Exception):
            pass

        with self.assertRaises(TestException):
            generator.throw(TestException)

        self.assertTrue(session.closed)

    def test_provider_signature_matches_session_provider_type(self) -> None:
        factory = FakeSessionFactory()
        provider = session_dependency(factory)

        result = provider()

        self.assertIsInstance(result, Generator)

    def test_closes_session_when_generator_is_exhausted(self) -> None:
        factory = FakeSessionFactory()
        provider = session_dependency(factory)

        generator = provider()
        next(generator)

        with self.assertRaises(StopIteration):
            next(generator)

        self.assertTrue(factory.calls[0].closed)


if __name__ == "__main__":
    unittest.main()
