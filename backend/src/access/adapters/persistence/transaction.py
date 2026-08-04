"""Transaction adapter wrapping SQLAlchemy session commit/rollback."""

from contextlib import contextmanager

from sqlalchemy.orm import Session


class TransactionAdapter:
    """Implements TransactionPort using the SQLAlchemy session.

    Commits on normal exit, rolls back on exception.
    When the session is shared with Auth (coordinated provisioning),
    the outermost transaction boundary controls commit.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @contextmanager
    def atomic(self):
        try:
            yield
            self._session.flush()
        except Exception:
            self._session.rollback()
            raise
