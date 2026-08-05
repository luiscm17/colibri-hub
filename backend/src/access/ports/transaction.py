"""Port for atomic transaction management."""

from contextlib import AbstractContextManager
from typing import Protocol


class TransactionPort(Protocol):
    """Commit application-owned Access changes atomically."""

    def atomic(self) -> AbstractContextManager[None]:
        """Return a context manager for a transactional boundary.

        Changes are committed on normal exit and rolled back on exception.
        """
        ...
