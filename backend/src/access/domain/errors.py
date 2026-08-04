"""Typed access control domain errors per tech spec §14.

Each error maps to a specific HTTP response code.
Errors never contain tokens, credentials, or provider secrets.
"""


class AccessError(Exception):
    """Base class for access control domain errors."""

    code: str = "access_error"


# --- 403 ---


class AccessDenied(AccessError):
    """Active user lacks the required exact permission. → 403"""

    code = "access_denied"

    def __init__(self) -> None:
        super().__init__("Access denied.")


class AccessUserInactive(AccessError):
    """Authenticated identity maps to an inactive user. → 403"""

    code = "access_user_inactive"

    def __init__(self) -> None:
        super().__init__("Access user is inactive.")


class AccessProfileNotFound(AccessError):
    """Authenticated identity has no Access profile. → 403"""

    code = "access_profile_not_found"

    def __init__(self) -> None:
        super().__init__("Access profile not found for this identity.")


# --- 404 ---


class AccessUserNotFound(AccessError):
    """Requested Access user does not exist. → 404"""

    code = "access_user_not_found"

    def __init__(self) -> None:
        super().__init__("Access user not found.")


class AccessRoleNotFound(AccessError):
    """Requested role does not exist. → 404"""

    code = "access_role_not_found"

    def __init__(self) -> None:
        super().__init__("Access role not found.")


class AccessScopeNotFound(AccessError):
    """Requested scope does not exist. → 404"""

    code = "access_scope_not_found"

    def __init__(self) -> None:
        super().__init__("Access scope not found.")


# --- 409 ---


class DuplicateAccessIdentity(AccessError):
    """Identity subject is already mapped. → 409"""

    code = "duplicate_access_identity"

    def __init__(self) -> None:
        super().__init__("An access profile with this identity subject already exists.")


class DuplicateUserCode(AccessError):
    """User code already exists. → 409"""

    code = "duplicate_access_user_code"

    def __init__(self) -> None:
        super().__init__("An access user with this user code already exists.")


class DuplicateRoleCode(AccessError):
    """Role code already exists. → 409"""

    code = "duplicate_access_role_code"

    def __init__(self) -> None:
        super().__init__("A role with this role code already exists.")


class DuplicateScopeCode(AccessError):
    """Scope code already exists. → 409"""

    code = "duplicate_access_scope_code"

    def __init__(self) -> None:
        super().__init__("A scope with this scope code already exists.")


class AccessVersionConflict(AccessError):
    """Expected version differs from persisted version. → 409"""

    code = "access_version_conflict"

    def __init__(self) -> None:
        super().__init__("The resource has been modified by another operation.")


class LastSystemAdministratorRequired(AccessError):
    """Mutation would leave no active System Administrator. → 409"""

    code = "last_system_administrator_required"

    def __init__(self) -> None:
        super().__init__("At least one active System Administrator must remain.")


class InactiveAccessRole(AccessError):
    """Assignment references an inactive role. → 409"""

    code = "inactive_access_role"

    def __init__(self) -> None:
        super().__init__("The referenced role is inactive.")


class InactiveAccessScope(AccessError):
    """Permission references an inactive scope. → 409"""

    code = "inactive_access_scope"

    def __init__(self) -> None:
        super().__init__("The referenced scope is inactive.")


# --- 422 ---


class InvalidAccessAction(AccessError):
    """Unsupported action value. → 422"""

    code = "invalid_access_action"

    def __init__(self) -> None:
        super().__init__("The action value is not supported.")


class UnsupportedActionForScope(AccessError):
    """Recognized scope does not support the requested action. → 422"""

    code = "unsupported_action_for_scope"

    def __init__(self) -> None:
        super().__init__("The recognized scope does not support this action.")


class UnrecognizedScopeDefinition(AccessError):
    """Registration references a definition not declared by the application. → 422"""

    code = "unrecognized_scope_definition"

    def __init__(self) -> None:
        super().__init__("The scope definition is not recognized by the application.")


class PrivilegedActionRequiresSystemAdministrator(AccessError):
    """Ordinary role or preset includes a reserved action. → 422"""

    code = "privileged_action_requires_system_administrator"

    def __init__(self) -> None:
        super().__init__("Only the System Administrator role may grant this action.")


class DuplicateRolePermission(AccessError):
    """Request repeats an action-and-scope pair. → 422"""

    code = "duplicate_role_permission"

    def __init__(self) -> None:
        super().__init__("Duplicate action and scope pair in permission set.")


class AccessChangeReasonRequired(AccessError):
    """Required administrative reason is absent. → 422"""

    code = "access_change_reason_required"

    def __init__(self) -> None:
        super().__init__("A reason is required for this administrative change.")


class ReservedRoleMutationForbidden(AccessError):
    """Request would alter reserved System Administrator semantics. → 422"""

    code = "reserved_role_mutation_forbidden"

    def __init__(self) -> None:
        super().__init__("The reserved System Administrator role cannot be modified.")
