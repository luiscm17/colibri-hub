"""Role and Assignment entities."""

from dataclasses import dataclass, field
from datetime import datetime

from access.domain.actions import PRIVILEGED_ACTIONS, Permission
from access.domain.errors import (
    AssignmentAlreadyRevoked,
    DuplicateRolePermission,
    PrivilegedActionRequiresSystemAdministrator,
)


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
        if not self.is_system_administrator and permission.action in PRIVILEGED_ACTIONS:
            raise PrivilegedActionRequiresSystemAdministrator()
        self.permissions.add(permission)

    def set_permissions(self, permissions: set[Permission]) -> None:
        """Full-replace the role's permission set.

        Validates that ordinary roles do not receive privileged actions.
        System Administrator roles accept any action.

        Raises:
            PrivilegedActionRequiresSystemAdministrator: if an ordinary role
                receives manage_access or edit_outside_window.
            DuplicateRolePermission: if the input set contains duplicates
                (impossible for a set, but kept for contract clarity).
        """
        if not self.is_system_administrator:
            for p in permissions:
                if p.action in PRIVILEGED_ACTIONS:
                    raise PrivilegedActionRequiresSystemAdministrator()
        self.permissions = set(permissions)

    def activate(self, *, at: datetime) -> None:
        """Reactivate the role. Idempotent when already active."""
        if self.is_active:
            return
        self.is_active = True
        self.version += 1
        self.updated_at = at

    def deactivate(self, *, at: datetime) -> None:
        """Deactivate the role. Idempotent when already inactive."""
        if not self.is_active:
            return
        self.is_active = False
        self.version += 1
        self.updated_at = at


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

    def revoke(self, *, by: str, reason: str | None, at: datetime) -> None:
        """Revoke this assignment. Raises if already revoked."""
        if not self.is_current:
            raise AssignmentAlreadyRevoked()
        self.revoked_by_user_id = by
        self.revoke_reason = reason
        self.revoked_at = at
