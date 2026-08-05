"""Use case: list registered scopes with pagination."""

from dataclasses import dataclass

from access.application.results import ScopeResult
from access.ports.scopes import ScopeRepository


@dataclass(frozen=True, slots=True)
class PaginatedScopes:
    items: list[ScopeResult]
    total: int


class ListScopes:
    def __init__(self, *, scope_repository: ScopeRepository) -> None:
        self._scopes = scope_repository

    def execute(
        self, *, page: int = 1, page_size: int = 50
    ) -> PaginatedScopes:
        offset = (page - 1) * page_size
        scopes = self._scopes.list_all(limit=page_size, offset=offset)
        total = self._scopes.count()
        return PaginatedScopes(
            items=[
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
            ],
            total=total,
        )
