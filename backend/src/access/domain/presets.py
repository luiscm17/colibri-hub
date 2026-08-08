"""Role preset aggregate used as a copy-only role template."""
from dataclasses import dataclass, field
from datetime import datetime
from access.domain.actions import PRIVILEGED_ACTIONS, Permission
from access.domain.errors import PrivilegedActionRequiresSystemAdministrator

@dataclass(frozen=True, slots=True)
class RolePresetPermission:
    permission: Permission

@dataclass(slots=True)
class RolePreset:
    preset_id: str
    preset_code: str
    preset_name: str
    description: str | None
    is_active: bool
    version: int
    permissions: set[Permission] = field(default_factory=set)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    def set_permissions(self, permissions: set[Permission]) -> None:
        if any(p.action in PRIVILEGED_ACTIONS for p in permissions): raise PrivilegedActionRequiresSystemAdministrator()
        self.permissions = set(permissions)
    def activate(self, *, at: datetime) -> None:
        if not self.is_active: self.is_active, self.version, self.updated_at = True, self.version + 1, at
    def deactivate(self, *, at: datetime) -> None:
        if self.is_active: self.is_active, self.version, self.updated_at = False, self.version + 1, at
