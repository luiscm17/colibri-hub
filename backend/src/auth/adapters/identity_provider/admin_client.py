"""Identity provider admin adapter.

All operations use the service_role key (server-only, never exposed to frontend).
Provider-specific request/response types do NOT cross this boundary — the port
returns provider-neutral DTOs.
"""

from __future__ import annotations

import logging
from typing import Any, Never, cast

from auth.domain.errors import (
    DuplicateEmail,
    IdentityConflict,
    ProviderUnavailable,
    WeakPassword,
)
from auth.ports.identity_provider import ProviderIdentity, ProviderSession
from supabase import Client as SupabaseClient

logger = logging.getLogger(__name__)


class IdentityProviderAdapter:
    """Server-side identity provider administration via service_role key."""

    def __init__(self, client: SupabaseClient) -> None:
        self._client = client

    def create_user(self, *, email: str, password: str) -> ProviderIdentity:
        """Create a provider identity without sending email confirmation."""
        try:
            response = self._client.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,  # Skip confirmation for admin-created accounts
                }
            )
            return ProviderIdentity(
                subject=str(response.user.id),
                email=response.user.email or email,
            )
        except Exception as exc:
            self._handle_provider_error(exc, context="create_user")

    def update_password(self, *, subject: str, new_password: str) -> None:
        """Update the credential for an existing provider identity."""
        try:
            self._client.auth.admin.update_user_by_id(
                subject, {"password": new_password}
            )
        except Exception as exc:
            self._handle_provider_error(exc, context="update_password")

    def ban_user(self, *, subject: str) -> None:
        """Prevent provider login for this identity."""
        try:
            self._client.auth.admin.update_user_by_id(
                subject, {"ban_duration": "876600h"}  # ~100 years
            )
        except Exception as exc:
            self._handle_provider_error(exc, context="ban_user")

    def unban_user(self, *, subject: str) -> None:
        """Restore provider login for this identity."""
        try:
            self._client.auth.admin.update_user_by_id(
                subject, {"ban_duration": "none"}
            )
        except Exception as exc:
            self._handle_provider_error(exc, context="unban_user")

    def revoke_sessions(self, *, subject: str) -> None:
        """Revoke all active provider sessions for this identity."""
        try:
            self._client.auth.admin.sign_out(subject, "global")
        except Exception as exc:
            # Session revocation is best-effort; log but don't fail
            logger.warning(
                "Failed to revoke sessions for subject %s: %s",
                subject,
                exc,
            )

    def get_session(self, *, session_id: str) -> ProviderSession | None:
        """Resolve provider-owned session by ID for age validation.

        Uses direct database query via service role since the admin API
        does not expose individual session lookup.
        """
        try:
            response = (
                self._client.schema("auth")
                .from_("sessions")
                .select("id, created_at, not_after")
                .eq("id", session_id)
                .execute()
            )

            data = response.data
            if not data:
                return None

            row = cast(dict[str, Any], data[0])
            return ProviderSession(
                session_id=str(row["id"]),
                created_at=row["created_at"],
                is_active=row.get("not_after") is None,
            )
        except Exception as exc:
            logger.warning(
                "Failed to resolve session %s: %s", session_id, exc
            )
            return None

    def delete_user(self, *, subject: str) -> None:
        """Remove a never-established identity as compensation."""
        try:
            self._client.auth.admin.delete_user(subject)
        except Exception as exc:
            logger.warning(
                "Failed to delete compensating identity %s: %s",
                subject,
                exc,
            )

    def _handle_provider_error(self, exc: Exception, *, context: str) -> Never:
        """Map provider errors to domain errors without exposing provider details.

        Raises:
            DuplicateEmail: On duplicate user creation.
            IdentityConflict: On conflicting identity state.
            WeakPassword: On password policy violation.
            ProviderUnavailable: On all other provider errors.
        """
        error_msg = str(exc).lower()

        if "duplicate" in error_msg or "already" in error_msg:
            if context == "create_user":
                raise DuplicateEmail() from exc
            raise IdentityConflict() from exc

        if "weak" in error_msg or "password" in error_msg and "short" in error_msg:
            raise WeakPassword() from exc

        logger.error(
            "Provider unavailable during %s: %s",
            context,
            type(exc).__name__,
            exc_info=False,
        )
        raise ProviderUnavailable() from exc
