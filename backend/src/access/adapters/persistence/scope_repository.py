"""Repository adapter for scope aggregate and scope definition registry."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from access.adapters.persistence.records import (
    AccessScopeDefinitionRecord,
    AccessScopeRecord,
)
from access.domain.actions import Action
from access.domain.scopes import Scope, ScopeDefinition


class ScopeRepositoryAdapter:
    """Resolves and persists scopes against access_scopes table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, scope_id: str) -> Scope | None:
        row = self._session.execute(
            select(AccessScopeRecord).where(
                AccessScopeRecord.scope_id == UUID(scope_id)
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def find_by_code(self, scope_code: str) -> Scope | None:
        row = self._session.execute(
            select(AccessScopeRecord).where(
                AccessScopeRecord.scope_code == scope_code
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def list_all(self) -> list[Scope]:
        rows = self._session.execute(
            select(AccessScopeRecord).order_by(AccessScopeRecord.created_at)
        ).scalars().all()
        return [self._to_domain(r) for r in rows]

    def save(self, scope: Scope) -> None:
        existing = self._session.execute(
            select(AccessScopeRecord).where(
                AccessScopeRecord.scope_id == UUID(scope.scope_id)
            )
        ).scalar_one_or_none()

        if existing is None:
            self._session.add(AccessScopeRecord(
                scope_id=UUID(scope.scope_id),
                definition_key=scope.definition_key,
                scope_code=scope.scope_code,
                scope_name=scope.scope_name,
                owning_context=scope.owning_context,
                description=scope.description,
                is_active=scope.is_active,
                version=scope.version,
                created_at=scope.created_at,
                updated_at=scope.updated_at,
            ))
        else:
            existing.is_active = scope.is_active
            existing.version = scope.version
            if scope.updated_at is not None:
                existing.updated_at = scope.updated_at

    @staticmethod
    def _to_domain(row: AccessScopeRecord) -> Scope:
        return Scope(
            scope_id=str(row.scope_id),
            definition_key=row.definition_key,
            scope_code=row.scope_code,
            scope_name=row.scope_name,
            owning_context=row.owning_context,
            description=row.description,
            is_active=row.is_active,
            version=row.version,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class ScopeDefinitionRegistryAdapter:
    """Reads from access_scope_definitions table (immutable catalog)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def all(self) -> list[ScopeDefinition]:
        rows = self._session.execute(
            select(AccessScopeDefinitionRecord).order_by(
                AccessScopeDefinitionRecord.definition_key
            )
        ).scalars().all()
        return [self._to_domain(r) for r in rows]

    def get(self, definition_key: str) -> ScopeDefinition | None:
        row = self._session.execute(
            select(AccessScopeDefinitionRecord).where(
                AccessScopeDefinitionRecord.definition_key == definition_key
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    @staticmethod
    def _to_domain(row: AccessScopeDefinitionRecord) -> ScopeDefinition:
        return ScopeDefinition(
            definition_key=row.definition_key,
            scope_code=row.scope_code,
            scope_name=row.scope_name,
            owning_context=row.owning_context,
            description=row.description,
            supported_actions=frozenset(Action(a) for a in row.supported_actions),
        )
