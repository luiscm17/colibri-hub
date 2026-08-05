"""Shared identity generator adapter for production use."""

from uuid import uuid4


class SystemIdentity:
    """Production identity generator using UUID4.

    Structurally satisfies any IdentityPort protocol requiring
    ``generate_id()`` and ``generate_operation_id()`` methods.
    """

    def generate_id(self) -> str:
        """Generate a unique identifier."""
        return str(uuid4())

    def generate_operation_id(self) -> str:
        """Generate a unique operation ID for correlating audits."""
        return str(uuid4())
