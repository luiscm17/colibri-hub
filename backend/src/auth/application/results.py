"""Result objects for authentication application use cases."""

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
