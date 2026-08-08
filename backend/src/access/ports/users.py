"""Repository protocol for access user aggregate."""

from typing import Protocol

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

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[AccessUser]:
        """Return access users ordered by creation time with optional pagination."""
        ...

    def count(self) -> int:
        """Return total count of access users."""
        ...

    def count_active_administrators(
        self, *, exclude_user_id: str | None = None, for_update: bool = False
    ) -> int:
        """Count active users with current assignment to the System Administrator role.

        When for_update is True, acquire row locks to prevent concurrent removal
        of the last administrator.
        """
        ...

    def bump_authorization_version_for_role(self, role_id: str) -> list[str]: ...
    def bump_authorization_version_for_scope(self, scope_id: str) -> list[str]: ...
