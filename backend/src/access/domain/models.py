"""Backward-compatibility bridge — removed in PR 4.

Re-exports spine-era types from new domain modules so that existing consumers
(application/services.py, adapters/persistence/store.py, warehouse_authorization.py)
compile without changes until they are replaced in later PRs.

DO NOT add new code here. DO NOT import from this module in new code.
"""

# Re-export Action (spine only used READ/WRITE; new enum has all 5)
from access.domain.actions import Action as Action

# Re-export ScopeCode value object (same shape, moved to scopes module)
from access.domain.scopes import ScopeCode as ScopeCode

# Spine-era types that have no direct equivalent in the new domain.
# These are used ONLY by services.py and store.py (eliminated in PR 3–4).
from dataclasses import dataclass


SYSTEM_ADMINISTRATOR = "system_administrator"
ACCESS_CONTROL = "access_control"
WAREHOUSE_RAW_MATERIALS = "warehouse.raw_materials"


@dataclass(frozen=True, slots=True)
class Permission:
    """Spine-era permission — uses ScopeCode value object."""

    action: Action
    scope: ScopeCode


@dataclass(slots=True)
class Scope:
    """Spine-era scope — flat code + active flag."""

    code: ScopeCode
    is_active: bool = True


@dataclass(slots=True)
class Role:
    """Spine-era role — flat code + permission set."""

    code: str
    permissions: frozenset[Permission] = frozenset()
    is_active: bool = True

    @property
    def is_system_administrator(self) -> bool:
        return self.code == SYSTEM_ADMINISTRATOR


@dataclass(slots=True)
class AccessProfile:
    """Spine-era access profile."""

    subject: str
    code: str
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.subject or not self.code:
            raise ValueError("Profile subject and code must be non-empty.")


@dataclass(slots=True)
class RoleAssignment:
    """Spine-era role assignment."""

    subject: str
    role_code: str
    is_active: bool = True
    is_current: bool = True


@dataclass(frozen=True, slots=True)
class AccessSnapshot:
    """Spine-era authorization snapshot."""

    subject: str
    profile_code: str
    global_access: bool
    permissions: frozenset[Permission]


def snapshot_for(
    subject: str,
    profiles: list[AccessProfile],
    roles: list[Role],
    scopes: list[Scope],
    assignments: list[RoleAssignment],
) -> AccessSnapshot | None:
    profile = next((item for item in profiles if item.subject == subject), None)
    if profile is None or not profile.is_active:
        return None
    active_scopes = {item.code for item in scopes if item.is_active}
    roles_by_code = {item.code: item for item in roles if item.is_active}
    current_roles = (
        roles_by_code.get(item.role_code)
        for item in assignments
        if item.subject == subject and item.is_current and item.is_active
    )
    resolved_roles = [role for role in current_roles if role is not None]
    if any(role.is_system_administrator for role in resolved_roles):
        return AccessSnapshot(subject, profile.code, True, frozenset())
    permissions = frozenset(
        permission
        for role in resolved_roles
        for permission in role.permissions
        if permission.scope in active_scopes
    )
    return AccessSnapshot(subject, profile.code, False, permissions)


def allows(
    snapshot: AccessSnapshot | None,
    action: Action,
    scope: ScopeCode,
    scopes: list[Scope],
) -> bool:
    if snapshot is None or scope not in {item.code for item in scopes if item.is_active}:
        return False
    return snapshot.global_access or Permission(action, scope) in snapshot.permissions
