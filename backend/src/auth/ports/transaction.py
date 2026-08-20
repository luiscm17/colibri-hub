"""Checkpoint contract owned by Authentication application policy."""

from typing import Protocol


class Transaction(Protocol):
    """Durably persist local denial before provider-side operations."""

    def commit(self) -> None:
        """Commit the current unit of work."""
        ...
