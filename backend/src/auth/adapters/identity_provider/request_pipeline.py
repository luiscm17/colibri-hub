"""Authentication request pipeline: account state + session age validation.

After JWT validation produces an AuthenticatedIdentity, this pipeline:
1. Resolves the local account from identity_subject.
2. Rejects disabled accounts even when the JWT is cryptographically valid.
3. Checks provider session age and rejects at the 8-hour boundary.
4. Restricts awaiting_password_change accounts to permitted endpoints only.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.errors import (
    AuthenticationFailed,
    AuthenticationRequired,
    PasswordChangeRequired,
)
from auth.ports.account_repository import AccountRepository
from auth.ports.identity_provider import IdentityProviderPort
from warehouse.bales.ports.authorization import AuthenticatedIdentity


SESSION_MAX_DURATION = timedelta(hours=8)

# Endpoints permitted for accounts in awaiting_password_change state
AWAITING_PERMITTED_PATHS = frozenset(
    {
        "/api/v1/auth/me",
        "/api/v1/auth/password-change",
        "/api/v1/auth/session",
    }
)


class RequestPipeline:
    """Validates account state and session age after JWT validation.

    Designed to be called as a FastAPI dependency after the JWT validator
    has produced an AuthenticatedIdentity.
    """

    def __init__(
        self,
        *,
        account_repository: AccountRepository,
        identity_provider: IdentityProviderPort,
    ) -> None:
        self._accounts = account_repository
        self._provider = identity_provider

    def validate(
        self,
        identity: AuthenticatedIdentity,
        request_path: str,
        request_method: str,
    ) -> AuthenticatedIdentity:
        """Run the full authentication pipeline after JWT validation.

        Returns the validated identity or raises an appropriate error.
        """
        # Resolve local account
        account = self._accounts.find_by_subject(identity.subject)
        if account is None:
            raise AuthenticationFailed()

        # Reject disabled accounts
        if account.status == AuthenticationAccountStatus.DISABLED:
            raise AuthenticationFailed()

        # Check session age (8-hour boundary)
        if identity.session_id:
            self._check_session_age(identity.session_id)

        # Restrict awaiting_password_change to permitted endpoints
        if account.status == AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE:
            if not self._is_permitted_for_awaiting(request_path, request_method):
                raise PasswordChangeRequired()

        return identity

    def _check_session_age(self, session_id: str) -> None:
        """Reject sessions older than 8 hours from provider start time."""
        session = self._provider.get_session(session_id=session_id)
        if session is None:
            # Session not found in provider — ended or revoked
            raise AuthenticationRequired()

        if not session.is_active:
            raise AuthenticationRequired()

        try:
            created_at = datetime.fromisoformat(session.created_at)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if now - created_at >= SESSION_MAX_DURATION:
                raise AuthenticationRequired()
        except (ValueError, TypeError):
            # If we cannot determine session age, deny conservatively
            raise AuthenticationRequired()

    @staticmethod
    def _is_permitted_for_awaiting(path: str, method: str) -> bool:
        """Check if the endpoint is accessible during mandatory password change."""
        # GET /auth/me is always permitted
        if path == "/api/v1/auth/me" and method.upper() == "GET":
            return True
        # POST /auth/password-change is always permitted
        if path == "/api/v1/auth/password-change" and method.upper() == "POST":
            return True
        # DELETE /auth/session (logout) is always permitted
        if path == "/api/v1/auth/session" and method.upper() == "DELETE":
            return True
        return False
