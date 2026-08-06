"""Use case: create a new configurable role."""

from access.application.commands import CreateRoleCommand
from access.application.results import PermissionResult, RoleResult
from access.domain.actions import PRIVILEGED_ACTIONS, Action, Permission
from access.domain.errors import (
    AccessScopeNotFound,
    DuplicateRoleCode,
    DuplicateRolePermission,
    InactiveAccessScope,
    PrivilegedActionRequiresSystemAdministrator,
    UnsupportedActionForScope,
)
from access.ports.clock import ClockPort
from access.ports.identity import IdentityPort
from access.ports.audit import AccessAuditRepository
from access.ports.roles import RoleRepository
from access.ports.scopes import ScopeDefinitionRegistry, ScopeRepository
from access.ports.transaction import TransactionPort


class CreateRole:
    """Create a new ordinary role with its permission set."""

    def __init__(
        self,
        *,
        role_repository: RoleRepository,
        scope_repository: ScopeRepository,
        scope_definition_registry: ScopeDefinitionRegistry,
        audit_repository: AccessAuditRepository,
        transaction: TransactionPort,
        clock: ClockPort,
        identity: IdentityPort,
    ) -> None:
        self._roles = role_repository
        self._scopes = scope_repository
        self._definitions = scope_definition_registry
        self._audits = audit_repository
        self._transaction = transaction
        self._clock = clock
        self._identity = identity

    def execute(self, command: CreateRoleCommand) -> RoleResult:
        with self._transaction.atomic():
            # Uniqueness
            if self._roles.find_by_code(command.role_code) is not None:
                raise DuplicateRoleCode()

            # Validate permissions
            permissions = self._validate_permissions(command.permissions)

            now = self._clock.now()
            from access.domain.roles import Role

            role = Role(
                role_id=self._identity.generate_id(),
                role_code=command.role_code,
                role_name=command.role_name,
                description=command.description,
                is_system_administrator=False,
                is_active=True,
                version=1,
                permissions=permissions,
                created_at=now,
                updated_at=now,
            )
            self._roles.save(role, created_by_user_id=command.actor_user_id)

            self._audits.append(
                operation_id=command.operation_id,
                change_kind="role_created",
                subject_type="role",
                subject_id=role.role_id,
                performed_by_user_id=command.actor_user_id,
                reason=command.reason,
                before_values={},
                after_values={
                    "role_code": role.role_code,
                    "role_name": role.role_name,
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
            is_system_administrator=False,
            is_active=True,
            version=1,
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
            # Valid action
            try:
                action = Action(p.action)
            except ValueError:
                from access.domain.errors import InvalidAccessAction
                raise InvalidAccessAction()

            # Privileged actions not allowed on ordinary roles
            if action in PRIVILEGED_ACTIONS:
                raise PrivilegedActionRequiresSystemAdministrator()

            # Scope exists and is active
            scope = self._scopes.find_by_id(p.scope_id)
            if scope is None:
                raise AccessScopeNotFound()
            if not scope.is_active:
                raise InactiveAccessScope()

            # Scope definition supports this action
            definition = self._definitions.get(scope.definition_key)
            if definition is not None and action not in definition.supported_actions:
                raise UnsupportedActionForScope()

            # Duplicate check
            pair = (p.action, p.scope_id)
            if pair in seen:
                raise DuplicateRolePermission()
            seen.add(pair)

            permissions.add(Permission(action=action, scope_code=scope.scope_code))

        return permissions
