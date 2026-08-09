"""Identity provider admin adapter.

All operations use the service_role key (server-only, never exposed to frontend).
Provider-specific request/response types do NOT cross this boundary — the port
returns provider-neutral DTOs.
"""

from __future__ import annotations

import logging
import json
from datetime import datetime
from typing import Any, Mapping, Never, cast
from uuid import UUID

from httpx import QueryParams
from auth.domain.errors import (
    DuplicateEmail,
    IdentityConflict,
    ProviderUnavailable,
    WeakPassword,
)
from auth.ports.identity_provider import (
    ProviderIdentity,
    ProviderLoginAuditEvidence,
    ProviderSession,
)
from supabase import Client as SupabaseClient

logger = logging.getLogger(__name__)

MAX_PROVIDER_AUDIT_ENTRIES = 500
MAX_PROVIDER_AUDIT_ENTRY_BYTES = 4096
MAX_PROVIDER_AUDIT_RESPONSE_BYTES = 2 + MAX_PROVIDER_AUDIT_ENTRIES * (
    MAX_PROVIDER_AUDIT_ENTRY_BYTES + 1
)


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
        """Revoke all active provider sessions for this identity.

        Uses direct deletion from auth.sessions via service-role schema
        query. This is the same mechanism used by get_session for lookups.
        """
        try:
            (
                self._client.schema("auth")
                .from_("sessions")
                .delete()
                .eq("user_id", subject)
                .execute()
            )
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

    def list_successful_login_audit_evidence(
        self, *, timestamp_to: str
    ) -> list[ProviderLoginAuditEvidence]:
        """Read a bounded recent login-evidence snapshot through Admin Audit.

        This adapter owns only provider projection. It deliberately does not
        inspect application accounts or expose provider payload data.
        """
        try:
            cutoff = self._parse_timestamp(timestamp_to)
            payload = json.loads(self._stream_audit_body(timestamp_to))
            entries = self._validate_audit_snapshot(payload, cutoff)
            evidence = [
                self._map_login_audit_entry(entry)
                for entry in entries
                if self._is_supported_login_entry(entry)
            ]
            return sorted(
                evidence,
                key=lambda item: (-self._parse_timestamp(item.occurred_at).timestamp(), item.entry_id),
            )
        except Exception as exc:
            logger.error(
                "Provider unavailable during list_successful_login_audit_evidence: %s",
                type(exc).__name__,
                exc_info=False,
            )
            raise ProviderUnavailable() from exc

    def _stream_audit_body(self, timestamp_to: str) -> bytes:
        """Stream the private GoTrue response with a pre-decode byte ceiling."""
        auth = self._client.auth
        with auth._http_client.stream(
            "GET",
            f"{auth._url}/admin/audit",
            params=QueryParams({"timestamp_to": timestamp_to}),
            headers=auth._headers,
        ) as response:
            if not 200 <= response.status_code < 300:
                raise ValueError("audit request failed")
            content_length = response.headers.get("Content-Length")
            if content_length and content_length.isdigit() and int(content_length) > MAX_PROVIDER_AUDIT_RESPONSE_BYTES:
                raise ValueError("audit response exceeds byte ceiling")
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > MAX_PROVIDER_AUDIT_RESPONSE_BYTES:
                    raise ValueError("audit response exceeds byte ceiling")
            return bytes(body)

    def _validate_audit_snapshot(
        self, payload: object, cutoff: datetime
    ) -> list[Mapping[str, object]]:
        if not isinstance(payload, list) or len(payload) > MAX_PROVIDER_AUDIT_ENTRIES:
            raise ValueError("invalid audit response")
        validated_entries: list[Mapping[str, object]] = []
        entry_ids: set[str] = set()
        for entry in payload:
            if not isinstance(entry, Mapping):
                raise ValueError("invalid audit entry")
            entry_id = entry.get("id")
            occurred_at = entry.get("created_at")
            audit_payload = entry.get("payload")
            if not isinstance(entry_id, str) or not entry_id or entry_id in entry_ids:
                raise ValueError("missing audit entry id")
            if not isinstance(occurred_at, str) or self._parse_timestamp(occurred_at) > cutoff:
                raise ValueError("invalid audit entry timestamp")
            if not isinstance(audit_payload, Mapping) or not isinstance(audit_payload.get("action"), str):
                raise ValueError("invalid audit entry payload")
            entry_ids.add(entry_id)
            validated_entries.append(entry)
        return validated_entries

    @staticmethod
    def _is_supported_login_entry(entry: Mapping[str, object]) -> bool:
        payload = entry.get("payload")
        return isinstance(payload, Mapping) and payload.get("action") == "login"

    @staticmethod
    def _map_login_audit_entry(
        entry: Mapping[str, object],
    ) -> ProviderLoginAuditEvidence:
        payload = cast(Mapping[str, object], entry["payload"])
        actor_id = payload.get("actor_id")
        subject = actor_id if isinstance(actor_id, str) and IdentityProviderAdapter._is_uuid(actor_id) else None
        return ProviderLoginAuditEvidence(
            entry_id=cast(str, entry["id"]),
            occurred_at=cast(str, entry["created_at"]),
            subject=subject,
            event_type="login_succeeded",
        )

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timestamp must include timezone")
        return parsed

    @staticmethod
    def _is_uuid(value: str) -> bool:
        try:
            UUID(value)
        except ValueError:
            return False
        return True

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
