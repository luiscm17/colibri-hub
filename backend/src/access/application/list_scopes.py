"""Use case: list all registered scopes."""

from access.application.results import ScopeResult
from access.ports.scopes import ScopeRepository


class ListScopes:
    def __init__(self, *, scope_repository: ScopeRepository) -> None:
        self._scopes = scope_repository

    def execute(self) -> list[ScopeResult]:
        scopes = self._scopes.list_all()
        return [
            ScopeResult(
                scope_id=s.scope_id,
                definition_key=s.definition_key,
                scope_code=s.scope_code,
                scope_name=s.scope_name,
                owning_context=s.owning_context,
                is_active=s.is_active,
                version=s.version,
            )
            for s in scopes
        ]
