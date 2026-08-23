"""Use case: deactivate an access user profile."""

from access.application.commands import (
    AdministrativeProfileLifecycleCommand,
    DeactivateAccessUserCommand,
)
from access.domain.errors import AccessUserNotFound
from access.ports.administrator_continuity import AdministratorContinuityPort
from access.ports.audit import AccessAuditRepository
from access.ports.clock import ClockPort
from access.ports.transaction import TransactionPort
from access.ports.users import AccessUserRepository


class DeactivateAccessUser:
    def __init__(
        self,
        *,
        user_repository: AccessUserRepository,
        audit_repository: AccessAuditRepository,
        transaction: TransactionPort,
        clock: ClockPort,
        continuity: AdministratorContinuityPort,
    ) -> None:
        self._users = user_repository
        self._audits = audit_repository
        self._transaction = transaction
        self._clock = clock
        self._continuity = continuity

    def execute(
        self,
        command: DeactivateAccessUserCommand | AdministrativeProfileLifecycleCommand,
    ) -> None:
        with self._transaction.atomic():
            user = self._users.find_by_subject(command.subject)
            if user is None:
                raise AccessUserNotFound()

            self._continuity.assert_reduction_allowed(user.identity_subject)

            before_active = user.is_active
            user.deactivate(at=self._clock.now())
            self._users.save(user)

            actor = self._users.find_by_subject(command.actor_subject)
            self._audits.append(
                operation_id=command.operation_id,
                change_kind="user_deactivated",
                subject_type="user",
                subject_id=user.user_id,
                performed_by_user_id=actor.user_id if actor else None,
                reason=command.reason,
                before_values={"is_active": before_active},
                after_values={"is_active": False},
            )
