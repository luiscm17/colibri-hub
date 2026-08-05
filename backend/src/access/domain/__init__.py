"""Access Control domain — public API.

Domain modules:
- actions: Action enum (5 values), Permission value object
- users: AccessUser entity
- roles: Role entity, Assignment entity with revocation lifecycle
- scopes: ScopeCode value object, Scope entity, ScopeDefinition catalog entry
- errors: typed domain exceptions
- authorization: effective_permissions(), authorize() evaluation functions
"""

from access.domain.actions import PRIVILEGED_ACTIONS as PRIVILEGED_ACTIONS
from access.domain.actions import Action as Action
from access.domain.actions import Permission as Permission
from access.domain.authorization import authorize as authorize
from access.domain.authorization import effective_permissions as effective_permissions
from access.domain.errors import (
    AccessChangeReasonRequired as AccessChangeReasonRequired,
)
from access.domain.errors import (
    AccessDenied as AccessDenied,
)
from access.domain.errors import (
    AccessError as AccessError,
)
from access.domain.errors import (
    AccessProfileNotFound as AccessProfileNotFound,
)
from access.domain.errors import (
    AccessRoleNotFound as AccessRoleNotFound,
)
from access.domain.errors import (
    AccessScopeNotFound as AccessScopeNotFound,
)
from access.domain.errors import (
    AccessUserInactive as AccessUserInactive,
)
from access.domain.errors import (
    AccessUserNotFound as AccessUserNotFound,
)
from access.domain.errors import (
    AccessVersionConflict as AccessVersionConflict,
)
from access.domain.errors import (
    DuplicateAccessIdentity as DuplicateAccessIdentity,
)
from access.domain.errors import (
    DuplicateRoleCode as DuplicateRoleCode,
)
from access.domain.errors import (
    DuplicateRolePermission as DuplicateRolePermission,
)
from access.domain.errors import (
    DuplicateScopeCode as DuplicateScopeCode,
)
from access.domain.errors import (
    DuplicateUserCode as DuplicateUserCode,
)
from access.domain.errors import (
    InactiveAccessRole as InactiveAccessRole,
)
from access.domain.errors import (
    InactiveAccessScope as InactiveAccessScope,
)
from access.domain.errors import (
    InvalidAccessAction as InvalidAccessAction,
)
from access.domain.errors import (
    LastSystemAdministratorRequired as LastSystemAdministratorRequired,
)
from access.domain.errors import (
    PrivilegedActionRequiresSystemAdministrator as PrivilegedActionRequiresSystemAdministrator,
)
from access.domain.errors import (
    ReservedRoleMutationForbidden as ReservedRoleMutationForbidden,
)
from access.domain.errors import (
    UnrecognizedScopeDefinition as UnrecognizedScopeDefinition,
)
from access.domain.errors import (
    UnsupportedActionForScope as UnsupportedActionForScope,
)
from access.domain.roles import Assignment as Assignment
from access.domain.roles import Role as Role
from access.domain.scopes import Scope as Scope
from access.domain.scopes import ScopeCode as ScopeCode
from access.domain.scopes import ScopeDefinition as ScopeDefinition
from access.domain.users import AccessUser as AccessUser
