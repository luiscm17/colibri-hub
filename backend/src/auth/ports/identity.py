"""Port for generating identifiers."""

from typing import Protocol


class IdentityPort(Protocol):
    """Generate internal identifiers and coordinated operation_id values."""

    def generate_id(self) -> str:
        """Generate a unique identifier (UUID)."""
        ...

    def generate_operation_id(self) -> str:
        """Generate a unique operation_id for correlating coordinated audits."""
        ...
