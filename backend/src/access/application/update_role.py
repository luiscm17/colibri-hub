"""Use case: update an existing role's configuration (full-replace permissions)."""

from access.application.commands import UpdateRoleCommand
from access.application.results import PermissionResult, RoleResult
from access.domain.actions import PRIVILEGED_ACTIONS, Action, Permission
from access.domain.errors import (
    AccessRoleNotFound,
    AccessScopeNotFound,
    AccessVersionConflict,
    DuplicateRolePermission,
    InactiveAccessScope,
    InvalidAccessAction,
    PrivilegedActionRequiresSystemAdministrator,
    ReservedRoleMutationForbidden,
    UnsupportedActionForScope,
)
from access.ports.audit import AccessAuditRepository
from access.ports.clock import ClockPort
from access.ports.roles import RoleRepository
from access.ports.scopes import ScopeDefinitionRegistry, ScopeRepository
from access.ports.transaction import TransactionPort


class UpdateRole:
    """Replace a role's name, description, and permission set."""

    def __init__(
        self,
        *,
        role_repository: RoleRepository,
        scope_repository: ScopeRepository,
        scope_definition_registry: ScopeDefinitionRegistry,
        audit_repository: AccessAuditRepository,
        transaction: TransactionPort,
        clock: ClockPort,
    ) -> None:
        self._roles = role_repository
        self._scopes = scope_repository
        self._definitions = scope_definition_registry
        self._audits = audit_repository
        self._transaction = transaction
        self._clock = clock

    def execute(self, command: UpdateRoleCommand) -> RoleResult:
        with self._transaction.atomic():
            role = self._roles.find_by_id(command.role_id)
            if role is None:
                raise AccessRoleNotFound()
            if role.is_system_administrator:
                raise ReservedRoleMutationForbidden()
            if role.version != command.expected_version:
                raise AccessVersionConflict()

            # Validate and build new permission set
            permissions = self._validate_permissions(command.permissions)

            before = {
                "role_name": role.role_name,
                "description": role.description,
                "permissions": [
                    {"action": p.action, "scope_code": p.scope_code}
                    for p in sorted(role.permissions, key=lambda x: (x.action, x.scope_code))
                ],
            }

            now = self._clock.now()
            role.role_name = command.role_name
            role.description = command.description
            role.set_permissions(permissions)
            role.version += 1
            role.updated_at = now
            self._roles.save(role)

            self._audits.append(
                operation_id=command.operation_id,
                change_kind="role_updated",
                subject_type="role",
                subject_id=role.role_id,
                performed_by_user_id=command.actor_user_id,
                reason=command.reason,
                before_values=before,
                after_values={
                    "role_name": role.role_name,
                    "description": role.description,
                    "permissions": [
                        {"action": p.action, "scope_code": p.scope_code}
                        for p in sorted(permissions, key=lambda x: (x.action, x.scope_code))
                    ],
                },
            )

        return RoleResult(
            role_id=role.role_id,
            role_code=role.role_code,
            role_name=role.role_name,
            description=role.description,
            is_system_administrator=role.is_system_administrator,
            is_active=role.is_active,
            version=role.version,
            permissions=[
                PermissionResult(action=p.action, scope_code=p.scope_code)
                for p in sorted(permissions, key=lambda x: (x.action, x.scope_code))
            ],
        )

    def _validate_permissions(self, inputs: list) -> set[Permission]:
        """Validate permission inputs against domain rules."""
        seen: set[tuple[str, str]] = set()
        permissions: set[Permission] = set()

        for p in inputs:
            try:
                action = Action(p.action)
            except ValueError:
                raise InvalidAccessAction()

            if action in PRIVILEGED_ACTIONS:
                raise PrivilegedActionRequiresSystemAdministrator()

            scope = self._scopes.find_by_id(p.scope_id)
            if scope is None:
                raise AccessScopeNotFound()
            if not scope.is_active:
                raise InactiveAccessScope()

            definition = self._definitions.get(scope.definition_key)
            if definition is not None and action not in definition.supported_actions:
                raise UnsupportedActionForScope()

            pair = (p.action, p.scope_id)
            if pair in seen:
                raise DuplicateRolePermission()
            seen.add(pair)

            permissions.add(Permission(action=action, scope_code=scope.scope_code))

        return permissions
