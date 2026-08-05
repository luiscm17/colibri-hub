"""Repository protocol for role aggregate."""

from typing import Protocol

from access.domain.roles import Role


class RoleRepository(Protocol):
    """Resolve and persist role state."""

    def find_by_id(self, role_id: str) -> Role | None:
        """Resolve a role by its internal identifier."""
        ...

    def find_by_code(self, role_code: str) -> Role | None:
        """Resolve a role by its unique code."""
        ...

    def find_system_administrator_role(self) -> Role | None:
        """Resolve the reserved System Administrator role."""
        ...

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[Role]:
        """Return roles ordered by creation time with optional pagination."""
        ...

    def count(self) -> int:
        """Return total count of roles."""
        ...

    def save(self, role: Role) -> None:
        """Persist a new or updated role. Raises on constraint violation."""
        ...
