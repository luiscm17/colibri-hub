"""Use case: resolve current user access snapshot for /access/me."""

from access.domain.actions import Action
from access.domain.authorization import effective_permissions
from access.domain.errors import AccessProfileNotFound, AccessUserInactive
from access.application.dto import CurrentAccessResult, PermissionResult
from access.ports.repositories import AccessUserRepository, RoleRepository, ScopeRepository


class GetCurrentAccess:
    """Return the authenticated user's effective access for the current session."""

    def __init__(
        self,
        *,
        user_repository: AccessUserRepository,
        role_repository: RoleRepository,
        scope_repository: ScopeRepository,
    ) -> None:
        self._users = user_repository
        self._roles = role_repository
        self._scopes = scope_repository

    def execute(self, *, subject: str) -> CurrentAccessResult:
        user = self._users.find_by_subject(subject)
        if user is None:
            raise AccessProfileNotFound()
        if not user.is_active:
            raise AccessUserInactive()

        assignments = self._roles.find_assignments_for_user(user.user_id)
        roles = [
            r for r in (self._roles.find_by_id(a.role_id) for a in assignments if a.is_current)
            if r is not None
        ]
        scopes = self._scopes.list_all()

        is_global = any(r.is_system_administrator for r in roles if r.is_active)
        perms = effective_permissions(user, assignments, roles, scopes)

        return CurrentAccessResult(
            user_id=user.user_id,
            user_code=user.user_code,
            display_name=user.display_name,
            is_active=user.is_active,
            is_global=is_global,
            permissions=[
                PermissionResult(action=p.action, scope_code=p.scope_code)
                for p in sorted(perms, key=lambda x: (x.action, x.scope_code))
            ],
            authorization_version=user.authorization_version,
        )
