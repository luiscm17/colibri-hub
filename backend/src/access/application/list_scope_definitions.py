"""Use case: list all recognized scope definitions with registration status."""

from access.application.dto import ScopeDefinitionResult
from access.ports.repositories import ScopeDefinitionRegistry, ScopeRepository


class ListScopeDefinitions:
    def __init__(
        self,
        *,
        scope_definition_registry: ScopeDefinitionRegistry,
        scope_repository: ScopeRepository,
    ) -> None:
        self._definitions = scope_definition_registry
        self._scopes = scope_repository

    def execute(self) -> list[ScopeDefinitionResult]:
        definitions = self._definitions.all()
        registered_codes = {s.scope_code for s in self._scopes.list_all()}

        return [
            ScopeDefinitionResult(
                definition_key=d.definition_key,
                scope_code=d.scope_code,
                scope_name=d.scope_name,
                owning_context=d.owning_context,
                description=d.description,
                supported_actions=sorted(d.supported_actions),
                is_registered=d.scope_code in registered_codes,
            )
            for d in sorted(definitions, key=lambda x: x.definition_key)
        ]
