"""Use case: reactivate a role."""

from access.application.commands import ActivateRoleCommand
from access.domain.errors import AccessRoleNotFound, AccessVersionConflict
from access.ports.audit import AccessAuditRepository
from access.ports.clock import ClockPort
from access.ports.roles import RoleRepository
from access.ports.transaction import TransactionPort
from access.ports.users import AccessUserRepository


class ActivateRole:
    """Reactivate a deactivated role."""

    def __init__(
        self,
        *,
        role_repository: RoleRepository,
        audit_repository: AccessAuditRepository,
        user_repository: AccessUserRepository | None = None,
        transaction: TransactionPort,
        clock: ClockPort,
    ) -> None:
        self._roles = role_repository
        self._audits = audit_repository
        self._users = user_repository
        self._transaction = transaction
        self._clock = clock

    def execute(self, command: ActivateRoleCommand) -> None:
        with self._transaction.atomic():
            role = self._roles.find_by_id(command.role_id)
            if role is None:
                raise AccessRoleNotFound()
            if role.version != command.expected_version:
                raise AccessVersionConflict()

            before_active = role.is_active
            role.activate(at=self._clock.now())
            self._roles.save(role)
            if self._users is not None:
                self._users.bump_authorization_version_for_role(role.role_id)

            self._audits.append(
                operation_id=command.operation_id,
                change_kind="role_activated",
                subject_type="role",
                subject_id=role.role_id,
                performed_by_user_id=command.actor_user_id,
                reason=command.reason,
                before_values={"is_active": before_active},
                after_values={"is_active": True},
            )
