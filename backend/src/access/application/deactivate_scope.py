"""Use case: deactivate a scope."""

from access.application.commands import DeactivateScopeCommand
from access.domain.errors import AccessScopeNotFound, AccessVersionConflict
from access.ports.audit import AccessAuditRepository
from access.ports.clock import ClockPort
from access.ports.scopes import ScopeRepository
from access.ports.transaction import TransactionPort


class DeactivateScope:
    """Deactivate a scope — it stops authorizing."""

    def __init__(
        self,
        *,
        scope_repository: ScopeRepository,
        audit_repository: AccessAuditRepository,
        transaction: TransactionPort,
        clock: ClockPort,
    ) -> None:
        self._scopes = scope_repository
        self._audits = audit_repository
        self._transaction = transaction
        self._clock = clock

    def execute(self, command: DeactivateScopeCommand) -> None:
        with self._transaction.atomic():
            scope = self._scopes.find_by_id(command.scope_id)
            if scope is None:
                raise AccessScopeNotFound()
            if scope.version != command.expected_version:
                raise AccessVersionConflict()

            before_active = scope.is_active
            scope.deactivate(at=self._clock.now())
            self._scopes.save(scope)

            self._audits.append(
                operation_id=command.operation_id,
                change_kind="scope_deactivated",
                subject_type="scope",
                subject_id=scope.scope_id,
                performed_by_user_id=command.actor_user_id,
                reason=command.reason,
                before_values={"is_active": before_active},
                after_values={"is_active": False},
            )
