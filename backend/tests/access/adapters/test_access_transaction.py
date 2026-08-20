"""Unit tests for the Access SQLAlchemy transaction adapter."""

import unittest
from typing import cast

from access.adapters.persistence.transaction import TransactionAdapter
from sqlalchemy.orm import Session


class SessionSpy:
    def __init__(self, commit_error: Exception | None = None) -> None:
        self._commit_error = commit_error
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1
        if self._commit_error is not None:
            raise self._commit_error

    def rollback(self) -> None:
        self.rollbacks += 1


class TestTransactionAdapterCheckpoint(unittest.TestCase):
    def test_commits_checkpoint(self) -> None:
        session = SessionSpy()

        TransactionAdapter(cast(Session, session)).commit()

        self.assertEqual(session.commits, 1)
        self.assertEqual(session.rollbacks, 0)

    def test_rolls_back_and_reraises_when_checkpoint_fails(self) -> None:
        error = RuntimeError("database unavailable")
        session = SessionSpy(error)

        with self.assertRaises(RuntimeError) as caught:
            TransactionAdapter(cast(Session, session)).commit()

        self.assertIs(caught.exception, error)
        self.assertEqual(session.commits, 1)
        self.assertEqual(session.rollbacks, 1)
