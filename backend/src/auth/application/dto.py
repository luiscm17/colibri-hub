"""Data transfer objects for authentication application use cases."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AccountSummary:
    """Non-secret account summary for API responses."""

    account_id: str
    email: str
    display_name: str
    user_code: str
    status: str
    version: int


@dataclass(frozen=True, slots=True)
class CurrentAuthenticationResult:
    """Result of inspecting the current authentication state."""

    account_id: str
    email: str
    display_name: str
    status: str
    next_step: str  # "change_password" or "load_access"


@dataclass(frozen=True, slots=True)
class ProvisionAccountCommand:
    """Command to provision a new account with coordinated Access profile."""

    email: str
    provisional_password: str
    user_code: str
    display_name: str
    role_codes: list[str]
    reason: str
    actor_subject: str


@dataclass(frozen=True, slots=True)
class ResetPasswordCommand:
    """Command to administratively reset a password."""

    account_id: str
    provisional_password: str
    reason: str
    expected_version: int
    actor_subject: str


@dataclass(frozen=True, slots=True)
class DisableAccountCommand:
    """Command to disable an account."""

    account_id: str
    reason: str
    expected_version: int
    actor_subject: str


@dataclass(frozen=True, slots=True)
class EnableAccountCommand:
    """Command to re-enable a disabled account."""

    account_id: str
    provisional_password: str
    reason: str
    expected_version: int
    actor_subject: str


@dataclass(frozen=True, slots=True)
class ChangePasswordCommand:
    """Command for mandatory password replacement."""

    current_password: str
    new_password: str
    actor_subject: str
    session_id: str | None
