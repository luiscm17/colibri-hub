"""Repository-backed, read-only impact preview query adapter."""

from dataclasses import replace

from access.domain.authorization import effective_permissions
from access.domain.errors import AccessRoleNotFound, AccessUserNotFound, InactiveAccessRole, LastSystemAdministratorRequired
from access.domain.roles import Assignment
from access.ports.assignments import AssignmentRepository
from access.ports.previews import PreviewResult, PreviewRole, PreviewUser
from access.ports.roles import RoleRepository
from access.ports.scopes import ScopeRepository
from access.ports.users import AccessUserRepository


class RepositoryPreviewQuery:
    """Computes net permission deltas from repository snapshots only."""

    def __init__(self, *, user_repository: AccessUserRepository, role_repository: RoleRepository, assignment_repository: AssignmentRepository, scope_repository: ScopeRepository) -> None:
        self._users = user_repository
        self._roles = role_repository
        self._assignments = assignment_repository
        self._scopes = scope_repository

    def preview_role_change(self, role_id: str, proposed: set) -> PreviewResult:
        role = self._roles.find_by_id(role_id)
        if role is None:
            raise AccessRoleNotFound()
        affected_users = []
        added, removed = set(), set()
        for assignment in self._assignments.find_for_role(role_id):
            user = self._users.find_by_id(assignment.user_id)
            if user is None:
                continue
            assignments = self._assignments.find_for_user(user.user_id)
            roles = [candidate for candidate in (self._roles.find_by_id(item.role_id) for item in assignments) if candidate]
            current = effective_permissions(user, assignments, roles, self._scopes.list_all())
            proposed_roles = [replace(candidate, permissions=proposed) if candidate.role_id == role_id else candidate for candidate in roles]
            resulting = effective_permissions(user, assignments, proposed_roles, self._scopes.list_all())
            added.update(resulting - current)
            removed.update(current - resulting)
            affected_users.append(PreviewUser(user.user_id, user.user_code, user.display_name))
        return PreviewResult(role.version, affected_users, frozenset(added), frozenset(removed), [], [])

    def preview_user_role_replacement(self, user_id: str, role_ids: list[str]) -> PreviewResult:
        user = self._users.find_by_id(user_id)
        if user is None:
            raise AccessUserNotFound()
        requested_roles = []
        for role_id in set(role_ids):
            role = self._roles.find_by_id(role_id)
            if role is None:
                raise AccessRoleNotFound()
            if not role.is_active:
                raise InactiveAccessRole()
            requested_roles.append(role)
        assignments = self._assignments.find_for_user(user_id)
        current_roles = [role for role in (self._roles.find_by_id(item.role_id) for item in assignments) if role]
        administrator = self._roles.find_system_administrator_role()
        current_ids, requested_ids = {role.role_id for role in current_roles}, {role.role_id for role in requested_roles}
        if administrator and administrator.role_id in current_ids and administrator.role_id not in requested_ids:
            if self._users.count_active_administrators(exclude_user_id=user_id, for_update=False) < 1:
                raise LastSystemAdministratorRequired()
        current = effective_permissions(user, assignments, current_roles, self._scopes.list_all())
        proposed_assignments = [Assignment(f"preview-{role.role_id}", user_id, role.role_id, "preview", user.updated_at) for role in requested_roles]
        resulting = effective_permissions(user, proposed_assignments, requested_roles, self._scopes.list_all())
        by_id = {role.role_id: role for role in current_roles + requested_roles}
        to_preview_role = lambda role_id: PreviewRole(role_id, by_id[role_id].role_code, by_id[role_id].role_name)
        return PreviewResult(
            user.version, [PreviewUser(user.user_id, user.user_code, user.display_name)],
            frozenset(resulting - current), frozenset(current - resulting),
            [to_preview_role(role_id) for role_id in sorted(requested_ids - current_ids)],
            [to_preview_role(role_id) for role_id in sorted(current_ids - requested_ids)],
        )
