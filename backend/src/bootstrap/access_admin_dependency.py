"""FastAPI dependency factory for Access Control admin use cases."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from access.adapters.persistence.repositories import (
    AccessAuditRepositoryAdapter,
    AccessUserRepositoryAdapter,
    RoleRepositoryAdapter,
    ScopeDefinitionRegistryAdapter,
    ScopeRepositoryAdapter,
)
from access.adapters.persistence.transaction import TransactionAdapter
from access.application.create_role import CreateRole
from access.application.list_access_audits import ListAccessAudits
from access.application.list_access_users import ListAccessUsers
from access.application.list_roles import ListRoles
from access.application.list_scope_definitions import ListScopeDefinitions
from access.application.list_scopes import ListScopes
from access.application.register_recognized_scope import RegisterRecognizedScope
from access.application.replace_user_roles import ReplaceUserRoles
from bootstrap.database_session_dependency import SessionProvider


class _SimpleIdentity:
    """Simple identity generator for operation IDs."""

    def generate_id(self) -> str:
        from uuid import uuid4
        return str(uuid4())

    def generate_operation_id(self) -> str:
        from uuid import uuid4
        return str(uuid4())


class _SimpleClock:
    """Simple clock for timestamps."""

    def now(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc)


def admin_use_case_dependency(
    session_provider: SessionProvider,
) -> Callable[..., dict]:
    """Build the request-scoped admin use case dict."""

    identity = _SimpleIdentity()
    clock = _SimpleClock()

    def provide(
        session: Annotated[Session, Depends(session_provider)],
    ) -> dict:
        user_repo = AccessUserRepositoryAdapter(session)
        role_repo = RoleRepositoryAdapter(session)
        scope_repo = ScopeRepositoryAdapter(session)
        definition_registry = ScopeDefinitionRegistryAdapter(session)
        audit_repo = AccessAuditRepositoryAdapter(session)
        transaction = TransactionAdapter(session)

        return {
            "list_access_users": ListAccessUsers(user_repository=user_repo),
            "list_roles": ListRoles(role_repository=role_repo),
            "list_scopes": ListScopes(scope_repository=scope_repo),
            "list_scope_definitions": ListScopeDefinitions(
                scope_definition_registry=definition_registry,
                scope_repository=scope_repo,
            ),
            "list_access_audits": ListAccessAudits(audit_repository=audit_repo),
            "create_role": CreateRole(
                role_repository=role_repo,
                scope_repository=scope_repo,
                scope_definition_registry=definition_registry,
                audit_repository=audit_repo,
                transaction=transaction,
                clock=clock,
                identity=identity,
            ),
            "replace_user_roles": ReplaceUserRoles(
                user_repository=user_repo,
                role_repository=role_repo,
                audit_repository=audit_repo,
                transaction=transaction,
                clock=clock,
                identity=identity,
            ),
            "register_recognized_scope": RegisterRecognizedScope(
                scope_repository=scope_repo,
                scope_definition_registry=definition_registry,
                audit_repository=audit_repo,
                transaction=transaction,
                clock=clock,
                identity=identity,
            ),
            "user_repository": user_repo,
            "identity": identity,
        }

    return provide
