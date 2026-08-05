"""Use case: register a recognized scope definition as an active scope."""

from access.application.dto import RegisterRecognizedScopeCommand, ScopeResult
from access.domain.errors import DuplicateScopeCode, UnrecognizedScopeDefinition
from access.ports.clock import ClockPort
from access.ports.identity import IdentityPort
from access.ports.repositories import (
    AccessAuditRepository,
    ScopeDefinitionRegistry,
    ScopeRepository,
)
from access.ports.transaction import TransactionPort


class RegisterRecognizedScope:
    """Register a scope from the immutable definition catalog.

    The backend supplies metadata from the definition — the client only sends
    the definition_key. Unknown definitions are rejected.
    """

    def __init__(
        self,
        *,
        scope_repository: ScopeRepository,
        scope_definition_registry: ScopeDefinitionRegistry,
        audit_repository: AccessAuditRepository,
        transaction: TransactionPort,
        clock: ClockPort,
        identity: IdentityPort,
    ) -> None:
        self._scopes = scope_repository
        self._definitions = scope_definition_registry
        self._audits = audit_repository
        self._transaction = transaction
        self._clock = clock
        self._identity = identity

    def execute(self, command: RegisterRecognizedScopeCommand) -> ScopeResult:
        with self._transaction.atomic():
            definition = self._definitions.get(command.definition_key)
            if definition is None:
                raise UnrecognizedScopeDefinition()

            # Already registered?
            existing = self._scopes.find_by_code(definition.scope_code)
            if existing is not None:
                raise DuplicateScopeCode()

            now = self._clock.now()
            from access.domain.scopes import Scope

            scope = Scope(
                scope_id=self._identity.generate_id(),
                definition_key=definition.definition_key,
                scope_code=definition.scope_code,
                scope_name=definition.scope_name,
                owning_context=definition.owning_context,
                description=definition.description,
                is_active=True,
                version=1,
                created_at=now,
                updated_at=now,
            )
            self._scopes.save(scope)

            self._audits.append(
                operation_id=command.operation_id,
                change_kind="scope_registered",
                subject_type="scope",
                subject_id=scope.scope_id,
                performed_by_user_id=command.actor_user_id,
                reason=command.reason,
                before_values={},
                after_values={
                    "definition_key": scope.definition_key,
                    "scope_code": scope.scope_code,
                },
            )

        return ScopeResult(
            scope_id=scope.scope_id,
            definition_key=scope.definition_key,
            scope_code=scope.scope_code,
            scope_name=scope.scope_name,
            owning_context=scope.owning_context,
            is_active=True,
            version=1,
        )
