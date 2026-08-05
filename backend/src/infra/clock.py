"""Shared clock adapter for production use."""

from datetime import datetime, timezone


class SystemClock:
    """Production clock supplying UTC timestamps.

    Structurally satisfies any ClockPort protocol requiring a ``now()``
    method that returns a timezone-aware ``datetime``.
    """

    def now(self) -> datetime:
        """Return the current UTC timestamp."""
        return datetime.now(timezone.utc)
