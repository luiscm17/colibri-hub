"""Authorization evaluation functions.

Correctness properties:
- Default-deny: if no matching permission exists, deny.
- Exact-match: scope codes have no inheritance (dot separator is naming only).
- Union: effective permissions = distinct union of all active assigned active roles.
- System Administrator: global access via policy branch, NOT permission rows.
"""

from access.domain.actions import Action, Permission
from access.domain.roles import Assignment, Role
from access.domain.scopes import Scope
from access.domain.users import AccessUser


def effective_permissions(
    user: AccessUser,
    assignments: list[Assignment],
    roles: list[Role],
    scopes: list[Scope],
) -> frozenset[Permission]:
    """Compute effective permissions for a user.

    Returns the distinct union of permissions from all active roles
    with current active assignments to this active user, filtered to
    active scopes.

    Args:
        user: The access user to compute permissions for.
        assignments: All assignments in the system.
        roles: All roles in the system.
        scopes: All registered scopes in the system.

    Returns:
        Frozen set of effective permissions, empty if user is inactive.
    """
    if not user.is_active:
        return frozenset()

    active_scope_codes: set[str] = {s.scope_code for s in scopes if s.is_active}
    roles_by_id: dict[str, Role] = {r.role_id: r for r in roles if r.is_active}

    # Resolve current assignments for this user
    user_assignments = [
        a for a in assignments
        if a.user_id == user.user_id and a.is_current
    ]

    resolved_roles = [
        roles_by_id[a.role_id]
        for a in user_assignments
        if a.role_id in roles_by_id
    ]

    # System Administrator gets all 5 actions in every active scope
    if any(r.is_system_administrator for r in resolved_roles):
        return frozenset(
            Permission(action=action, scope_code=scope_code)
            for scope_code in active_scope_codes
            for action in Action
        )

    # Ordinary: distinct union filtered to active scopes
    return frozenset(
        permission
        for role in resolved_roles
        for permission in role.permissions
        if permission.scope_code in active_scope_codes
    )


def authorize(
    user: AccessUser,
    action: Action,
    scope_code: str,
    assignments: list[Assignment],
    roles: list[Role],
    scopes: list[Scope],
) -> bool:
    """Evaluate authorization — returns True if allowed.

    Evaluation order:
        1. Deny if user is inactive.
        2. Allow if user is an active System Administrator.
        3. Deny if scope is absent or inactive.
        4. Allow if exact (action, scope_code) permission exists.
        5. Deny otherwise.

    Args:
        user: The access user requesting authorization.
        action: The action being requested.
        scope_code: The scope code to authorize within.
        assignments: All assignments in the system.
        roles: All roles in the system.
        scopes: All registered scopes in the system.

    Returns:
        True if the request is authorized, False otherwise.
    """
    if not user.is_active:
        return False

    active_scope_codes: set[str] = {s.scope_code for s in scopes if s.is_active}
    roles_by_id: dict[str, Role] = {r.role_id: r for r in roles if r.is_active}

    user_assignments = [
        a for a in assignments
        if a.user_id == user.user_id and a.is_current
    ]

    resolved_roles = [
        roles_by_id[a.role_id]
        for a in user_assignments
        if a.role_id in roles_by_id
    ]

    # Step 3 — System Administrator: global access via policy branch
    if any(r.is_system_administrator for r in resolved_roles):
        return True

    # Step 4 — Deny if scope is absent or inactive
    if scope_code not in active_scope_codes:
        return False

    # Steps 5-7 — Exact match from ordinary roles
    required = Permission(action=action, scope_code=scope_code)
    for role in resolved_roles:
        if required in role.permissions:
            return True

    return False
