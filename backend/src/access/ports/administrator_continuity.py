"""Port for Access-owned administrator continuity enforcement."""

from typing import Protocol


class AdministratorContinuityPort(Protocol):
    """Atomically reject a mutation that would breach the operational floor."""

    def assert_reduction_allowed(self, subject: str) -> None:
        """Lock continuity state and reject a projected two-to-one reduction."""
        ...
