"""Typed containers for composed use case dependencies."""

from dataclasses import dataclass

from access.application.activate_access_user import ActivateAccessUser
from access.application.activate_role import ActivateRole
from access.application.activate_scope import ActivateScope
from access.application.create_role import CreateRole
from access.application.deactivate_access_user import DeactivateAccessUser
from access.application.deactivate_role import DeactivateRole
from access.application.deactivate_scope import DeactivateScope
from access.application.get_access_user import GetAccessUser
from access.application.list_access_audits import ListAccessAudits
from access.application.list_access_users import ListAccessUsers
from access.application.list_roles import ListRoles
from access.application.list_scope_definitions import ListScopeDefinitions
from access.application.list_scopes import ListScopes
from access.application.register_recognized_scope import RegisterRecognizedScope
from access.application.replace_user_roles import ReplaceUserRoles
from access.application.update_role import UpdateRole
from access.ports import AccessUserRepository, IdentityPort, RoleRepository


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
    update_role: UpdateRole
    activate_role: ActivateRole
    deactivate_role: DeactivateRole
    activate_scope: ActivateScope
    deactivate_scope: DeactivateScope
    get_access_user: GetAccessUser
    activate_access_user: ActivateAccessUser
    deactivate_access_user: DeactivateAccessUser
    replace_user_roles: ReplaceUserRoles
    register_recognized_scope: RegisterRecognizedScope
    user_repository: AccessUserRepository
    role_repository: RoleRepository
    identity: IdentityPort
