"""Role and Assignment entities."""

from dataclasses import dataclass, field
from datetime import datetime

from access.domain.actions import Permission
from access.domain.errors import AssignmentAlreadyRevoked, DuplicateRolePermission


@dataclass(slots=True)
class Role:
    """Configurable role with an associated permission set."""

    role_id: str
    role_code: str
    role_name: str
    description: str | None
    is_system_administrator: bool
    is_active: bool
    version: int
    permissions: set[Permission] = field(default_factory=set)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def grant_permission(self, permission: Permission) -> None:
        """Add a permission to the role. Raises if already present."""
        if permission in self.permissions:
            raise DuplicateRolePermission()
        self.permissions.add(permission)


@dataclass(slots=True)
class Assignment:
    """A user-to-role assignment with revocation lifecycle."""

    assignment_id: str
    user_id: str
    role_id: str
    assigned_by_user_id: str
    assigned_at: datetime
    revoked_by_user_id: str | None = None
    revoked_at: datetime | None = None
    revoke_reason: str | None = None

    @property
    def is_current(self) -> bool:
        """An assignment is current when it has not been revoked."""
        return self.revoked_at is None

    def revoke(self, *, by: str, reason: str, at: datetime) -> None:
        """Revoke this assignment. Raises if already revoked."""
        if not self.is_current:
            raise AssignmentAlreadyRevoked()
        self.revoked_by_user_id = by
        self.revoke_reason = reason
        self.revoked_at = at
