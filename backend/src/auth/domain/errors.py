"""Typed authentication domain errors.

Each error maps to a specific HTTP response code per tech spec §15.
Errors never contain passwords, tokens, or provider secrets.
"""


class AuthenticationError(Exception):
    """Base class for authentication domain errors."""

    code: str = "authentication_error"


class AuthenticationRequired(AuthenticationError):
    """Bearer token absent, invalid, or expired. → 401"""

    code = "authentication_required"

    def __init__(self) -> None:
        super().__init__("Authentication is required.")


class AuthenticationFailed(AuthenticationError):
    """Provider login cannot establish an enabled identity. → 401"""

    code = "authentication_failed"

    def __init__(self) -> None:
        super().__init__("Authentication failed.")


class PasswordChangeRequired(AuthenticationError):
    """Protected operation attempted before mandatory replacement. → 403"""

    code = "password_change_required"

    def __init__(self) -> None:
        super().__init__(
            "Password change is required before accessing protected capabilities."
        )


class AccountNotFound(AuthenticationError):
    """Administrative target does not exist. → 404"""

    code = "authentication_account_not_found"

    def __init__(self, account_id: str) -> None:
        super().__init__("Authentication account not found.")
        self.account_id = account_id


class DuplicateEmail(AuthenticationError):
    """Email already exists. → 409"""

    code = "duplicate_authentication_email"

    def __init__(self) -> None:
        super().__init__("An account with this email already exists.")


class VersionConflict(AuthenticationError):
    """Expected version is stale. → 409"""

    code = "authentication_version_conflict"

    def __init__(self) -> None:
        super().__init__("The account has been modified by another operation.")


class AdministratorContinuityRequired(AuthenticationError):
    """Mutation would leave fewer than two operational administrators. → 409"""

    code = "administrator_continuity_required"

    def __init__(self) -> None:
        super().__init__("At least two operational System Administrators must remain.")


LastSystemAdministratorRequired = AdministratorContinuityRequired


class AccountStateConflict(AuthenticationError):
    """Transition is invalid from the current account state. → 409"""

    code = "authentication_account_state_conflict"

    def __init__(self, current_status: str, attempted_action: str) -> None:
        super().__init__(f"Cannot {attempted_action} from state '{current_status}'.")
        self.current_status = current_status
        self.attempted_action = attempted_action


class IdentityConflict(AuthenticationError):
    """Provider subject maps inconsistently. → 409"""

    code = "authentication_identity_conflict"

    def __init__(self) -> None:
        super().__init__("Identity subject mapping conflict.")


class ReplacementPasswordMustDiffer(AuthenticationError):
    """Replacement equals provisional password. → 422"""

    code = "replacement_password_must_differ"

    def __init__(self) -> None:
        super().__init__("The new password must differ from the current password.")


class CurrentPasswordRejected(AuthenticationError):
    """Submitted current password was not verified by the provider. → 401"""

    code = "current_password_rejected"

    def __init__(self) -> None:
        super().__init__("The current password is incorrect.")


class WeakPassword(AuthenticationError):
    """Provider password policy rejects the value with a redacted 422 outcome."""

    code = "weak_password"

    def __init__(self) -> None:
        super().__init__("The password does not meet security requirements.")


class ChangeReasonRequired(AuthenticationError):
    """Administrative reason is absent. → 422"""

    code = "authentication_change_reason_required"

    def __init__(self) -> None:
        super().__init__("A reason is required for administrative changes.")


class ProviderUnavailable(AuthenticationError):
    """Provider operation failed safely and may be retried. → 503"""

    code = "authentication_provider_unavailable"

    def __init__(self) -> None:
        super().__init__("The authentication provider is temporarily unavailable.")
