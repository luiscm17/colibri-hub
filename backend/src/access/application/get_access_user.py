"""Use case: get a single access user with assignments and effective permissions."""

from access.application.results import (
    AccessUserResult,
    AssignmentResult,
    PermissionResult,
    RoleSummaryResult,
)
from access.domain.authorization import effective_permissions
from access.domain.errors import AccessUserNotFound
from access.ports.assignments import AssignmentRepository
from access.ports.roles import RoleRepository
from access.ports.scopes import ScopeRepository
from access.ports.users import AccessUserRepository


class GetAccessUser:
    """Return a single user's profile, assignments, and effective permissions."""

    def __init__(
        self,
        *,
        user_repository: AccessUserRepository,
        role_repository: RoleRepository,
        assignment_repository: AssignmentRepository,
        scope_repository: ScopeRepository,
    ) -> None:
        self._users = user_repository
        self._roles = role_repository
        self._assignments = assignment_repository
        self._scopes = scope_repository

    def execute(self, *, user_id: str) -> "AccessUserDetailResult":
        user = self._users.find_by_id(user_id)
        if user is None:
            raise AccessUserNotFound()

        assignments = self._assignments.find_for_user(user.user_id)
        roles = [
            r for r in (self._roles.find_by_id(a.role_id) for a in assignments if a.is_current)
            if r is not None
        ]
        scopes = self._scopes.list_all()

        is_global = any(r.is_system_administrator for r in roles if r.is_active)
        perms = effective_permissions(user, assignments, roles, scopes)

        role_summaries = [
            RoleSummaryResult(role_id=r.role_id, code=r.role_code, name=r.role_name)
            for r in roles
            if r.is_active
        ]

        current_assignments = [
            AssignmentResult(
                assignment_id=a.assignment_id,
                role_id=a.role_id,
                role_code=next((r.role_code for r in roles if r.role_id == a.role_id), ""),
                role_name=next((r.role_name for r in roles if r.role_id == a.role_id), ""),
                assigned_at=a.assigned_at.isoformat(),
            )
            for a in assignments
            if a.is_current
        ]

        return AccessUserDetailResult(
            user=AccessUserResult(
                user_id=user.user_id,
                identity_subject=user.identity_subject,
                user_code=user.user_code,
                display_name=user.display_name,
                is_active=user.is_active,
                authorization_version=user.authorization_version,
                version=user.version,
            ),
            roles=role_summaries,
            assignments=current_assignments,
            is_global=is_global,
            permissions=[
                PermissionResult(action=p.action, scope_code=p.scope_code)
                for p in sorted(perms, key=lambda x: (x.action, x.scope_code))
            ],
        )


from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AccessUserDetailResult:
    """Full user detail with assignments and effective permissions."""

    user: AccessUserResult
    roles: list[RoleSummaryResult]
    assignments: list[AssignmentResult]
    is_global: bool
    permissions: list[PermissionResult]
