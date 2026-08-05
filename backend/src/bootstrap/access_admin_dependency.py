"""FastAPI dependency factory for Access Control admin use cases."""

from collections.abc import Callable
from typing import Annotated

from access.adapters.persistence.repositories import (
    AccessAuditRepositoryAdapter,
    AccessUserRepositoryAdapter,
    AssignmentRepositoryAdapter,
    RoleRepositoryAdapter,
    ScopeDefinitionRegistryAdapter,
    ScopeRepositoryAdapter,
)
from access.adapters.persistence.transaction import TransactionAdapter
from access.application.containers import AdminUseCases
from access.application.create_role import CreateRole
from access.application.list_access_audits import ListAccessAudits
from access.application.list_access_users import ListAccessUsers
from access.application.list_roles import ListRoles
from access.application.list_scope_definitions import ListScopeDefinitions
from access.application.list_scopes import ListScopes
from access.application.register_recognized_scope import RegisterRecognizedScope
from access.application.replace_user_roles import ReplaceUserRoles
from fastapi import Depends
from infra.clock import SystemClock
from infra.identity import SystemIdentity
from sqlalchemy.orm import Session

from bootstrap.database_session_dependency import SessionProvider


def admin_use_case_dependency(
    session_provider: SessionProvider,
) -> Callable[..., AdminUseCases]:
    """Build the request-scoped admin use case container."""

    identity = SystemIdentity()
    clock = SystemClock()

    def provide(
        session: Annotated[Session, Depends(session_provider)],
    ) -> AdminUseCases:
        user_repo = AccessUserRepositoryAdapter(session)
        role_repo = RoleRepositoryAdapter(session)
        scope_repo = ScopeRepositoryAdapter(session)
        assignment_repo = AssignmentRepositoryAdapter(session)
        definition_registry = ScopeDefinitionRegistryAdapter(session)
        audit_repo = AccessAuditRepositoryAdapter(session)
        transaction = TransactionAdapter(session)

        return AdminUseCases(
            list_access_users=ListAccessUsers(user_repository=user_repo),
            list_roles=ListRoles(role_repository=role_repo),
            list_scopes=ListScopes(scope_repository=scope_repo),
            list_scope_definitions=ListScopeDefinitions(
                scope_definition_registry=definition_registry,
                scope_repository=scope_repo,
            ),
            list_access_audits=ListAccessAudits(audit_repository=audit_repo),
            create_role=CreateRole(
                role_repository=role_repo,
                scope_repository=scope_repo,
                scope_definition_registry=definition_registry,
                audit_repository=audit_repo,
                transaction=transaction,
                clock=clock,
                identity=identity,
            ),
            replace_user_roles=ReplaceUserRoles(
                user_repository=user_repo,
                role_repository=role_repo,
                assignment_repository=assignment_repo,
                audit_repository=audit_repo,
                transaction=transaction,
                clock=clock,
                identity=identity,
            ),
            register_recognized_scope=RegisterRecognizedScope(
                scope_repository=scope_repo,
                scope_definition_registry=definition_registry,
                audit_repository=audit_repo,
                transaction=transaction,
                clock=clock,
                identity=identity,
            ),
            user_repository=user_repo,
            identity=identity,
        )

    return provide
