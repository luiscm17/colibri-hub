"""Repository protocols for access control aggregates."""

from typing import Protocol

from access.domain.audit import AccessAuditEntry
from access.domain.roles import Role
from access.domain.scopes import Scope, ScopeDefinition
from access.domain.users import AccessUser


class AccessUserRepository(Protocol):
    """Resolve and persist access user state."""

    def find_by_subject(self, identity_subject: str) -> AccessUser | None:
        """Resolve an access user by their external identity subject."""
        ...

    def find_by_id(self, user_id: str) -> AccessUser | None:
        """Resolve an access user by their internal identifier."""
        ...

    def save(self, user: AccessUser) -> None:
        """Persist a new or updated access user. Raises on constraint violation."""
        ...

    def list_all(self) -> list[AccessUser]:
        """Return all access users ordered by creation time."""
        ...

    def count_active_administrators(
        self, *, exclude_user_id: str | None = None, for_update: bool = False
    ) -> int:
        """Count active users with current assignment to the System Administrator role.

        When for_update is True, acquire row locks to prevent concurrent removal
        of the last administrator.
        """
        ...


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

    def list_all(self) -> list[Role]:
        """Return all roles ordered by creation time."""
        ...

    def save(self, role: Role) -> None:
        """Persist a new or updated role. Raises on constraint violation."""
        ...


class ScopeRepository(Protocol):
    """Resolve and persist scope state."""

    def find_by_id(self, scope_id: str) -> Scope | None:
        """Resolve a scope by its internal identifier."""
        ...

    def find_by_code(self, scope_code: str) -> Scope | None:
        """Resolve a scope by its exact code."""
        ...

    def list_all(self) -> list[Scope]:
        """Return all registered scopes."""
        ...

    def save(self, scope: Scope) -> None:
        """Persist a new or updated scope. Raises on constraint violation."""
        ...


class ScopeDefinitionRegistry(Protocol):
    """Expose the immutable set of product-recognized scope definitions."""

    def all(self) -> list[ScopeDefinition]:
        """Return all recognized scope definitions."""
        ...

    def get(self, definition_key: str) -> ScopeDefinition | None:
        """Resolve a scope definition by its unique key."""
        ...


class AccessAuditRepository(Protocol):
    """Append immutable access-change audit evidence."""

    def append(
        self,
        *,
        operation_id: str,
        change_kind: str,
        subject_type: str,
        subject_id: str,
        performed_by_user_id: str | None,
        reason: str | None,
        before_values: dict,
        after_values: dict,
    ) -> None:
        """Record one audit entry. Append-only — updates and deletes are forbidden."""
        ...

    def list_recent(self, *, limit: int = 50) -> list[AccessAuditEntry]:
        """Return recent audit entries ordered by occurred_at descending."""
        ...
