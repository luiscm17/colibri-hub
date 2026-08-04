"""Access Control domain — public API.

Domain modules:
- actions: Action enum (5 values), Permission value object
- users: AccessUser entity
- roles: Role entity, Assignment entity with revocation lifecycle
- scopes: ScopeCode value object, Scope entity, ScopeDefinition catalog entry
- errors: typed exceptions per tech spec §14
- authorization: effective_permissions(), authorize() evaluation functions
"""

from access.domain.actions import Action as Action
from access.domain.actions import PRIVILEGED_ACTIONS as PRIVILEGED_ACTIONS
from access.domain.actions import Permission as Permission
from access.domain.authorization import authorize as authorize
from access.domain.authorization import effective_permissions as effective_permissions
from access.domain.errors import (
    AccessChangeReasonRequired as AccessChangeReasonRequired,
    AccessDenied as AccessDenied,
    AccessError as AccessError,
    AccessProfileNotFound as AccessProfileNotFound,
    AccessRoleNotFound as AccessRoleNotFound,
    AccessScopeNotFound as AccessScopeNotFound,
    AccessUserInactive as AccessUserInactive,
    AccessUserNotFound as AccessUserNotFound,
    AccessVersionConflict as AccessVersionConflict,
    DuplicateAccessIdentity as DuplicateAccessIdentity,
    DuplicateRoleCode as DuplicateRoleCode,
    DuplicateRolePermission as DuplicateRolePermission,
    DuplicateScopeCode as DuplicateScopeCode,
    DuplicateUserCode as DuplicateUserCode,
    InactiveAccessRole as InactiveAccessRole,
    InactiveAccessScope as InactiveAccessScope,
    InvalidAccessAction as InvalidAccessAction,
    LastSystemAdministratorRequired as LastSystemAdministratorRequired,
    PrivilegedActionRequiresSystemAdministrator as PrivilegedActionRequiresSystemAdministrator,
    ReservedRoleMutationForbidden as ReservedRoleMutationForbidden,
    UnrecognizedScopeDefinition as UnrecognizedScopeDefinition,
    UnsupportedActionForScope as UnsupportedActionForScope,
)
from access.domain.roles import Assignment as Assignment
from access.domain.roles import Role as Role
from access.domain.scopes import Scope as Scope
from access.domain.scopes import ScopeCode as ScopeCode
from access.domain.scopes import ScopeDefinition as ScopeDefinition
from access.domain.users import AccessUser as AccessUser
