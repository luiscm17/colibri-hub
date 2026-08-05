"""Role and Assignment entities."""

from dataclasses import dataclass, field
from datetime import datetime

from access.domain.actions import Permission


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
