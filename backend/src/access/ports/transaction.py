"""Port for atomic transaction management."""

from contextlib import contextmanager
from typing import Protocol


class TransactionPort(Protocol):
    """Commit application-owned Access changes atomically."""

    @contextmanager
    def atomic(self):
        """Context manager for a transactional boundary.

        Changes are committed on normal exit and rolled back on exception.
        """
        ...
