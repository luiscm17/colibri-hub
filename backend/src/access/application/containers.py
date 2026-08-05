"""Typed containers for composed use case dependencies."""

from dataclasses import dataclass

from access.application.create_role import CreateRole
from access.application.list_access_audits import ListAccessAudits
from access.application.list_access_users import ListAccessUsers
from access.application.list_roles import ListRoles
from access.application.list_scope_definitions import ListScopeDefinitions
from access.application.list_scopes import ListScopes
from access.application.register_recognized_scope import RegisterRecognizedScope
from access.application.replace_user_roles import ReplaceUserRoles
from access.ports import AccessUserRepository, IdentityPort


@dataclass(frozen=True, slots=True)
class AdminUseCases:
    """Typed container for admin use case dependencies.

    Replaces the stringly-typed dict that was returned by the bootstrap
    dependency factory, providing attribute access with full type safety.
    """

    list_access_users: ListAccessUsers
    list_roles: ListRoles
    list_scopes: ListScopes
    list_scope_definitions: ListScopeDefinitions
    list_access_audits: ListAccessAudits
    create_role: CreateRole
    replace_user_roles: ReplaceUserRoles
    register_recognized_scope: RegisterRecognizedScope
    user_repository: AccessUserRepository
    identity: IdentityPort
