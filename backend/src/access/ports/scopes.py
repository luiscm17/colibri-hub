"""Repository protocol for scope aggregate and scope definition registry."""

from typing import Protocol

from access.domain.scopes import Scope, ScopeDefinition


class ScopeRepository(Protocol):
    """Resolve and persist scope state."""

    def find_by_id(self, scope_id: str) -> Scope | None:
        """Resolve a scope by its internal identifier."""
        ...

    def find_by_code(self, scope_code: str) -> Scope | None:
        """Resolve a scope by its exact code."""
        ...

    def list_all(self) -> list[Scope]:
        """Return all registered scopes."""
        ...

    def save(self, scope: Scope) -> None:
        """Persist a new or updated scope. Raises on constraint violation."""
        ...


class ScopeDefinitionRegistry(Protocol):
    """Expose the immutable set of product-recognized scope definitions."""

    def all(self) -> list[ScopeDefinition]:
        """Return all recognized scope definitions."""
        ...

    def get(self, definition_key: str) -> ScopeDefinition | None:
        """Resolve a scope definition by its unique key."""
        ...
