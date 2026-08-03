"""Authentication account entity with status transitions and immutability rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.email import NormalizedEmail
from auth.domain.errors import AccountStateConflict


@dataclass(slots=True)
class AuthenticationAccount:
    """Application-owned authentication account.

    Tracks identity subject, normalized email, lifecycle status, and
    optimistic-concurrency version. Passwords and tokens are never stored here.
    """

    account_id: str
    identity_subject: str
    normalized_email: NormalizedEmail
    status: AuthenticationAccountStatus
    display_name: str
    user_code: str
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def provision(
        cls,
        *,
        account_id: str,
        identity_subject: str,
        email: NormalizedEmail,
        display_name: str,
        user_code: str,
        now: datetime,
    ) -> AuthenticationAccount:
        """Create a new account in awaiting_password_change state."""
        return cls(
            account_id=account_id,
            identity_subject=identity_subject,
            normalized_email=email,
            status=AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE,
            display_name=display_name,
            user_code=user_code,
            version=1,
            created_at=now,
            updated_at=now,
        )

    def activate(self, now: datetime) -> None:
        """Transition from awaiting_password_change to active after mandatory replacement."""
        if self.status != AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE:
            raise AccountStateConflict(self.status.value, "activate")
        self.status = AuthenticationAccountStatus.ACTIVE
        self._bump_version(now)

    def disable(self, now: datetime) -> None:
        """Transition to disabled. Valid from awaiting_password_change or active."""
        if self.status == AuthenticationAccountStatus.DISABLED:
            raise AccountStateConflict(self.status.value, "disable")
        self.status = AuthenticationAccountStatus.DISABLED
        self._bump_version(now)

    def reset_to_awaiting(self, now: datetime) -> None:
        """Move active account to awaiting_password_change (administrative reset)."""
        if self.status != AuthenticationAccountStatus.ACTIVE:
            raise AccountStateConflict(self.status.value, "reset")
        self.status = AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE
        self._bump_version(now)

    def enable(self, now: datetime) -> None:
        """Re-enable a disabled account to awaiting_password_change."""
        if self.status != AuthenticationAccountStatus.DISABLED:
            raise AccountStateConflict(self.status.value, "enable")
        self.status = AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE
        self._bump_version(now)

    @property
    def is_enabled(self) -> bool:
        """An account is enabled if it is not disabled."""
        return self.status != AuthenticationAccountStatus.DISABLED

    @property
    def requires_password_change(self) -> bool:
        """Whether the account must replace its provisional password."""
        return self.status == AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE

    def check_version(self, expected_version: int) -> bool:
        """Validate optimistic concurrency version."""
        return self.version == expected_version

    def _bump_version(self, now: datetime) -> None:
        self.version += 1
        self.updated_at = now
