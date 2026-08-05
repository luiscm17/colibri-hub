"""Use case: deactivate a role."""

from access.application.commands import DeactivateRoleCommand
from access.domain.errors import (
    AccessRoleNotFound,
    AccessVersionConflict,
    ReservedRoleMutationForbidden,
)
from access.ports.audit import AccessAuditRepository
from access.ports.clock import ClockPort
from access.ports.roles import RoleRepository
from access.ports.transaction import TransactionPort


class DeactivateRole:
    """Deactivate a role — its permissions stop contributing."""

    def __init__(
        self,
        *,
        role_repository: RoleRepository,
        audit_repository: AccessAuditRepository,
        transaction: TransactionPort,
        clock: ClockPort,
    ) -> None:
        self._roles = role_repository
        self._audits = audit_repository
        self._transaction = transaction
        self._clock = clock

    def execute(self, command: DeactivateRoleCommand) -> None:
        with self._transaction.atomic():
            role = self._roles.find_by_id(command.role_id)
            if role is None:
                raise AccessRoleNotFound()
            if role.is_system_administrator:
                raise ReservedRoleMutationForbidden()
            if role.version != command.expected_version:
                raise AccessVersionConflict()

            before_active = role.is_active
            role.deactivate(at=self._clock.now())
            self._roles.save(role)

            self._audits.append(
                operation_id=command.operation_id,
                change_kind="role_deactivated",
                subject_type="role",
                subject_id=role.role_id,
                performed_by_user_id=command.actor_user_id,
                reason=command.reason,
                before_values={"is_active": before_active},
                after_values={"is_active": False},
            )
