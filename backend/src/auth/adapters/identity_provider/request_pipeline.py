"""Authentication request pipeline: account and provider-session validation.

After JWT validation produces an AuthenticatedIdentity, this pipeline:
1. Resolves the application account from identity_subject.
2. Rejects disabled accounts even when the JWT is cryptographically valid.
3. Checks that the provider session remains active for the verified subject.
4. Restricts awaiting_password_change accounts to permitted endpoints only.
"""

from __future__ import annotations

from shared.identity import AuthenticatedIdentity

from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.errors import (
    AuthenticationFailed,
    AuthenticationRequired,
    PasswordChangeRequired,
)
from auth.ports.account_repository import AuthAccountRepository
from auth.ports.identity_provider import IdentityProviderPort

# Endpoints permitted for accounts in awaiting_password_change state
AWAITING_PERMITTED_PATHS = frozenset(
    {
        "/api/v1/auth/me",
        "/api/v1/auth/password-change",
        "/api/v1/auth/session",
    }
)


class RequestPipeline:
    """Validates account state and provider session after JWT validation.

    Designed to be called as a FastAPI dependency after the JWT validator
    has produced an AuthenticatedIdentity.
    """

    def __init__(
        self,
        *,
        account_repository: AuthAccountRepository,
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
        # Resolve application account
        account = self._accounts.find_by_subject(identity.subject)
        if account is None:
            raise AuthenticationFailed()

        # Reject disabled accounts
        if account.status == AuthenticationAccountStatus.DISABLED:
            raise AuthenticationFailed()

        # Check provider-owned session state
        if identity.session_id:
            self._check_provider_session(
                session_id=identity.session_id,
                subject=identity.subject,
            )

        # Restrict awaiting_password_change to permitted endpoints
        if (
            account.status == AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE
            and not self._is_permitted_for_awaiting(request_path, request_method)
        ):
            raise PasswordChangeRequired()

        return identity

    def _check_provider_session(
        self,
        *,
        session_id: str,
        subject: str,
    ) -> None:
        """Reject missing, revoked, or mismatched provider sessions."""
        if not self._provider.has_active_session(
            session_id=session_id,
            subject=subject,
        ):
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
        return path == "/api/v1/auth/session" and method.upper() == "DELETE"
