"""Use case: evaluate an authorization request per §6.6."""

from access.domain.actions import Action
from access.domain.authorization import authorize
from access.domain.errors import AccessDenied, AccessProfileNotFound, AccessUserInactive
from access.ports.repositories import AccessUserRepository, RoleRepository, ScopeRepository


class AuthorizeAction:
    """Evaluate whether a subject may perform an action in a scope.

    Evaluation order (§6.6):
    1. Resolve identity to access user.
    2. Deny if user is absent or inactive.
    3. Allow if System Administrator.
    4. Deny if scope is absent or inactive.
    5. Allow if exact (action, scope) permission exists.
    6. Deny otherwise.
    """

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

    def execute(self, *, subject: str, action: str, scope_code: str) -> None:
        """Raises AccessDenied, AccessProfileNotFound, or AccessUserInactive."""
        user = self._users.find_by_subject(subject)
        if user is None:
            raise AccessProfileNotFound()
        if not user.is_active:
            raise AccessUserInactive()

        parsed_action = Action(action)
        assignments = self._roles.find_assignments_for_user(user.user_id)
        roles = [
            r for r in (self._roles.find_by_id(a.role_id) for a in assignments if a.is_current)
            if r is not None
        ]
        scopes = self._scopes.list_all()

        if not authorize(user, parsed_action, scope_code, assignments, roles, scopes):
            raise AccessDenied()
