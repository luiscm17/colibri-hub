"""Request and response models for Authentication HTTP endpoints.

Responses:
    AuthMeResponse: Current authentication state for the verified identity.
    AccountResponse: Administrative account detail with version.

Requests:
    PasswordChangeRequest: Mandatory password replacement (write-only fields).
    ProvisionAccountRequest: Unified account and access provisioning.
    ResetPasswordRequest: Administrative password reset.
    DisableAccountRequest: Account disablement.
    EnableAccountRequest: Account re-enablement.
"""

from pydantic import BaseModel, ConfigDict


class _AuthModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class AuthMeResponse(_AuthModel):
    """Current authentication state for the verified identity.

    Attributes:
        account_id: Internal account identifier.
        email: Normalized organizational email.
        display_name: Human-readable display name.
        status: Current account lifecycle state.
        next_step: Required action — "change_password" or "load_access".
    """

    account_id: str
    email: str
    display_name: str
    status: str
    next_step: str


class AccountResponse(_AuthModel):
    """Administrative account detail response.

    Attributes:
        account_id: Internal account identifier.
        email: Normalized organizational email.
        display_name: Human-readable display name.
        user_code: Organization-assigned user code.
        status: Current account lifecycle state.
        version: Optimistic-concurrency version for administrative mutations.
    """

    account_id: str
    email: str
    display_name: str
    user_code: str
    status: str
    version: int


class PasswordChangeRequest(_AuthModel):
    """Mandatory password replacement request.

    Both fields are write-only — never echoed in responses, logs, or audits.

    Attributes:
        current_password: The provisional password to replace.
        new_password: The replacement password (must differ from current).
    """

    current_password: str
    new_password: str


class ProvisionAccountRequest(_AuthModel):
    """Unified account and access provisioning request.

    Attributes:
        email: Organizational email for the new account.
        provisional_password: Write-only initial credential.
        user_code: Organization-assigned user code.
        display_name: Human-readable display name.
        role_codes: Initial Access Control roles to assign.
        reason: Administrative reason for provisioning.
    """

    email: str
    provisional_password: str
    user_code: str
    display_name: str
    role_codes: list[str]
    reason: str


class ResetPasswordRequest(_AuthModel):
    """Administrative password reset request.

    Attributes:
        provisional_password: Write-only new provisional credential.
        reason: Administrative reason for the reset.
        expected_version: Optimistic-concurrency guard.
    """

    provisional_password: str
    reason: str
    expected_version: int


class DisableAccountRequest(_AuthModel):
    """Account disablement request.

    Attributes:
        reason: Administrative reason for disablement.
        expected_version: Optimistic-concurrency guard.
    """

    reason: str
    expected_version: int


class EnableAccountRequest(_AuthModel):
    """Account re-enablement request.

    Attributes:
        provisional_password: Write-only new provisional credential.
        reason: Administrative reason for re-enablement.
        expected_version: Optimistic-concurrency guard.
    """

    provisional_password: str
    reason: str
    expected_version: int


class AuditEntryResponse(_AuthModel):
    """Authentication audit entry response.

    Attributes:
        audit_id: Unique audit entry identifier.
        operation_id: Correlated operation identifier.
        event_type: Type of authentication event.
        outcome: Result of the operation.
        affected_account_id: Account affected by the event, if any.
        occurred_at: ISO 8601 timestamp of the event.
    """

    audit_id: str
    operation_id: str
    event_type: str
    outcome: str
    affected_account_id: str | None
    occurred_at: str | None
