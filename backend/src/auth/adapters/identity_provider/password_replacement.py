"""Gate-selected Supabase implementation of mandatory password replacement."""

from __future__ import annotations

from sqlalchemy.orm import Session
from supabase_auth.errors import AuthError

from auth.adapters.identity_provider.admin_client import IdentityProviderAdapter
from auth.domain.errors import (
    CurrentPasswordRejected,
    ProviderUnavailable,
    WeakPassword,
)
from supabase import create_client

_WEAK_PASSWORD_POLICY_CODE = "weak_password"


class SupabasePasswordReplacementAdapter:
    """Compose verified reauthentication, replacement, and session termination.

    The application sees this adapter only through ``PasswordReplacementPort``.
    It never delegates credential mutation to the administrative identity adapter.
    """

    def __init__(
        self,
        *,
        provider_url: str,
        service_role_key: str,
        database_session: Session,
    ) -> None:
        self._provider_url = provider_url
        self._service_role_key = service_role_key
        self._database_session = database_session
        self._admin_client = create_client(provider_url, service_role_key)

    def replace_required_password(
        self,
        *,
        subject: str,
        session_id: str | None,
        current_password: str,
        new_password: str,
    ) -> None:
        """Verify current credentials before replacing and terminating the bearer.

        A disposable provider client verifies the submitted credential and owns
        the mutation. The provider terminates the original authenticated session
        after provider-confirmed replacement; this adapter verifies that result
        and never falls back to administrative session revocation.
        """
        if session_id is None:
            raise ProviderUnavailable()

        email = self._email_for_subject(subject)
        verification_client = create_client(self._provider_url, self._service_role_key)
        self._verify_current_password(
            verification_client,
            email=email,
            subject=subject,
            current_password=current_password,
        )

        try:
            verification_client.auth.update_user(
                {"password": new_password, "current_password": current_password}
            )
        except AuthError as exc:
            if exc.code == _WEAK_PASSWORD_POLICY_CODE:
                raise WeakPassword() from exc
            raise ProviderUnavailable() from exc
        except Exception as exc:
            raise ProviderUnavailable() from exc

        try:
            verification_client.auth.sign_out()
            original_session_is_active = IdentityProviderAdapter(
                self._admin_client, self._database_session
            ).has_active_session(session_id=session_id, subject=subject)
        except Exception as exc:
            raise ProviderUnavailable() from exc
        if original_session_is_active:
            raise ProviderUnavailable()

    def _email_for_subject(self, subject: str) -> str:
        try:
            response = self._admin_client.auth.admin.get_user_by_id(subject)
            email = response.user.email if response.user is not None else None
        except Exception as exc:
            raise ProviderUnavailable() from exc
        if not email:
            raise ProviderUnavailable()
        return email

    @staticmethod
    def _verify_current_password(
        client,
        *,
        email: str,
        subject: str,
        current_password: str,
    ) -> None:
        try:
            response = client.auth.sign_in_with_password(
                {"email": email, "password": current_password}
            )
        except AuthError as exc:
            raise CurrentPasswordRejected() from exc
        except Exception as exc:
            raise ProviderUnavailable() from exc

        if response.session is None or response.user is None:
            raise ProviderUnavailable()
        if str(response.user.id) != subject:
            raise ProviderUnavailable()
