"""Port for clock abstraction."""

from datetime import datetime
from typing import Protocol


class ClockPort(Protocol):
    """Supply timestamps for domain operations."""

    def now(self) -> datetime:
        """Return the current UTC timestamp."""
        ...
