"""Repository protocol for role assignment lifecycle."""

from typing import Protocol

from access.domain.roles import Assignment


class AssignmentRepository(Protocol):
    """Persist and query user-role assignments independently of roles."""

    def find_for_user(self, user_id: str) -> list[Assignment]:
        """Return all current assignments for a given user."""
        ...

    def find_for_role(self, role_id: str) -> list[Assignment]:
        """Return all current assignments for a given role."""
        ...

    def save(self, assignment: Assignment) -> None:
        """Persist a new or updated assignment."""
        ...
