"""Use case: reactivate a scope."""

from access.application.commands import ActivateScopeCommand
from access.domain.errors import AccessScopeNotFound, AccessVersionConflict
from access.ports.audit import AccessAuditRepository
from access.ports.clock import ClockPort
from access.ports.scopes import ScopeRepository
from access.ports.transaction import TransactionPort
from access.ports.users import AccessUserRepository


class ActivateScope:
    """Reactivate a deactivated scope."""

    def __init__(
        self,
        *,
        scope_repository: ScopeRepository,
        audit_repository: AccessAuditRepository,
        user_repository: AccessUserRepository | None = None,
        transaction: TransactionPort,
        clock: ClockPort,
    ) -> None:
        self._scopes = scope_repository
        self._audits = audit_repository
        self._users = user_repository
        self._transaction = transaction
        self._clock = clock

    def execute(self, command: ActivateScopeCommand) -> None:
        with self._transaction.atomic():
            scope = self._scopes.find_by_id(command.scope_id)
            if scope is None:
                raise AccessScopeNotFound()
            if scope.version != command.expected_version:
                raise AccessVersionConflict()

            before_active = scope.is_active
            scope.activate(at=self._clock.now())
            self._scopes.save(scope)
            if self._users is not None:
                self._users.bump_authorization_version_for_scope(scope.scope_id)

            self._audits.append(
                operation_id=command.operation_id,
                change_kind="scope_activated",
                subject_type="scope",
                subject_id=scope.scope_id,
                performed_by_user_id=command.actor_user_id,
                reason=command.reason,
                before_values={"is_active": before_active},
                after_values={"is_active": True},
            )
