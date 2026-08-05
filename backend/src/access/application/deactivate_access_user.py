"""Use case: deactivate an access user profile."""

from access.application.dto import DeactivateAccessUserCommand
from access.domain.errors import AccessUserNotFound, LastSystemAdministratorRequired
from access.ports.clock import ClockPort
from access.ports.repositories import AccessAuditRepository, AccessUserRepository
from access.ports.transaction import TransactionPort


class DeactivateAccessUser:
    def __init__(
        self,
        *,
        user_repository: AccessUserRepository,
        audit_repository: AccessAuditRepository,
        transaction: TransactionPort,
        clock: ClockPort,
    ) -> None:
        self._users = user_repository
        self._audits = audit_repository
        self._transaction = transaction
        self._clock = clock

    def execute(self, command: DeactivateAccessUserCommand) -> None:
        with self._transaction.atomic():
            user = self._users.find_by_subject(command.subject)
            if user is None:
                raise AccessUserNotFound()

            # Last-admin invariant
            remaining = self._users.count_active_administrators(
                exclude_user_id=user.user_id, for_update=True
            )
            if remaining < 1:
                raise LastSystemAdministratorRequired()

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
