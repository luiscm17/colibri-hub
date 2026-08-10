"""Unit tests for IdentityProviderAdapter (admin_client.py).

Validates that each adapter method calls the correct Supabase client
methods with the correct arguments and translates errors to domain types.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from httpx import QueryParams

from auth.adapters.identity_provider.admin_client import (
    MAX_PROVIDER_AUDIT_RESPONSE_BYTES,
    IdentityProviderAdapter,
)
from auth.domain.errors import DuplicateEmail, ProviderUnavailable, WeakPassword
from auth.ports.identity_provider import ProviderLoginAuditEvidence


class TestBanUser(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.adapter = IdentityProviderAdapter(self.client)

    def test_calls_update_user_by_id_with_ban_duration(self):
        self.adapter.ban_user(subject="user-uuid-123")

        self.client.auth.admin.update_user_by_id.assert_called_once_with(
            "user-uuid-123", {"ban_duration": "876600h"}
        )

    def test_raises_provider_unavailable_on_error(self):
        self.client.auth.admin.update_user_by_id.side_effect = Exception(
            "connection timeout"
        )

        with self.assertRaises(ProviderUnavailable):
            self.adapter.ban_user(subject="user-uuid-123")


class TestUnbanUser(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.adapter = IdentityProviderAdapter(self.client)

    def test_calls_update_user_by_id_with_none_duration(self):
        self.adapter.unban_user(subject="user-uuid-456")

        self.client.auth.admin.update_user_by_id.assert_called_once_with(
            "user-uuid-456", {"ban_duration": "none"}
        )

    def test_raises_provider_unavailable_on_error(self):
        self.client.auth.admin.update_user_by_id.side_effect = Exception(
            "network error"
        )

        with self.assertRaises(ProviderUnavailable):
            self.adapter.unban_user(subject="user-uuid-456")


class TestRevokeSessions(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.adapter = IdentityProviderAdapter(self.client)

    def test_calls_schema_auth_sessions_delete(self):
        """revoke_sessions must DELETE from auth.sessions WHERE user_id = subject."""
        mock_schema = MagicMock()
        mock_from = MagicMock()
        mock_delete = MagicMock()
        mock_eq = MagicMock()

        self.client.schema.return_value = mock_schema
        mock_schema.from_.return_value = mock_from
        mock_from.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_eq

        self.adapter.revoke_sessions(subject="user-uuid-789")

        self.client.schema.assert_called_once_with("auth")
        mock_schema.from_.assert_called_once_with("sessions")
        mock_from.delete.assert_called_once()
        mock_delete.eq.assert_called_once_with("user_id", "user-uuid-789")
        mock_eq.execute.assert_called_once()

    def test_does_not_reraise_on_exception(self):
        """revoke_sessions is best-effort — exceptions are swallowed."""
        self.client.schema.side_effect = Exception("db unavailable")

        # Should not raise
        self.adapter.revoke_sessions(subject="user-uuid-789")

    @patch("auth.adapters.identity_provider.admin_client.logger")
    def test_logs_warning_on_exception(self, mock_logger):
        """revoke_sessions logs a warning when it fails."""
        self.client.schema.side_effect = Exception("timeout")

        self.adapter.revoke_sessions(subject="user-uuid-789")

        mock_logger.warning.assert_called_once()
        args = mock_logger.warning.call_args[0]
        self.assertIn("user-uuid-789", args[1])


class TestHandleProviderError(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.adapter = IdentityProviderAdapter(self.client)

    def test_maps_duplicate_to_duplicate_email_in_create_user(self):
        with self.assertRaises(DuplicateEmail):
            self.adapter._handle_provider_error(
                Exception("duplicate key value"), context="create_user"
            )

    def test_maps_weak_password(self):
        with self.assertRaises(WeakPassword):
            self.adapter._handle_provider_error(
                Exception("weak password"), context="create_user"
            )

    def test_maps_unknown_error_to_provider_unavailable(self):
        with self.assertRaises(ProviderUnavailable):
            self.adapter._handle_provider_error(
                Exception("some random error"), context="ban_user"
            )


class _StreamResponse:
    def __init__(self, chunks, *, status_code=200, content_length=None):
        self._chunks = chunks
        self.status_code = status_code
        self.headers = {} if content_length is None else {"Content-Length": str(content_length)}

    def iter_bytes(self):
        yield from self._chunks


class _StreamContext:
    def __init__(self, response):
        self.response = response

    def __enter__(self):
        return self.response

    def __exit__(self, *_):
        return False


class TestListSuccessfulLoginAuditEvidence(unittest.TestCase):
    timestamp_to = "2026-08-09T12:00:00Z"

    def setUp(self):
        self.client = MagicMock()
        self.client.auth._url = "http://provider.test/auth/v1"
        self.client.auth._headers = {"Authorization": "Bearer test"}
        self.adapter = IdentityProviderAdapter(self.client)

    def _respond_with(self, payload, *, content_length=None, status_code=200):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.client.auth._http_client.stream.return_value = _StreamContext(
            _StreamResponse([body], status_code=status_code, content_length=content_length)
        )

    @staticmethod
    def _entry(entry_id="entry-1", action="login"):
        return {
            "id": entry_id,
            "created_at": "2026-08-09T11:00:00Z",
            "payload": {"action": action, "actor_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"},
        }

    def test_maps_only_allow_listed_success_fields(self):
        entry = self._entry()
        entry["payload"].update({"actor_username": "private@example.com", "access_token": "secret"})
        self._respond_with([entry])

        evidence = self.adapter.list_successful_login_audit_evidence(
            timestamp_to=self.timestamp_to
        )

        self.assertEqual(
            evidence,
            [
                ProviderLoginAuditEvidence(
                    entry_id="entry-1",
                    occurred_at="2026-08-09T11:00:00Z",
                    subject="f47ac10b-58cc-4372-a567-0e02b2c3d479",
                    event_type="login_succeeded",
                )
            ],
        )
        self.client.auth._http_client.stream.assert_called_once_with(
            "GET",
            "http://provider.test/auth/v1/admin/audit",
            params=QueryParams({"timestamp_to": self.timestamp_to}),
            headers={"Authorization": "Bearer test"},
        )

    def test_excludes_unsupported_provider_events(self):
        self._respond_with([self._entry("failed", "login_failed"), self._entry("refresh", "logout")])

        evidence = self.adapter.list_successful_login_audit_evidence(
            timestamp_to=self.timestamp_to
        )

        self.assertEqual(evidence, [])

    def test_does_not_access_application_account_persistence(self):
        self._respond_with([])

        self.adapter.list_successful_login_audit_evidence(
            timestamp_to=self.timestamp_to
        )

        self.client.schema.assert_not_called()
        self.client.from_.assert_not_called()

    def test_orders_by_occurred_at_desc_then_entry_id_asc(self):
        newer = self._entry("newer")
        newer["created_at"] = "2026-08-09T11:01:00Z"
        self._respond_with([self._entry("zeta"), newer, self._entry("alpha")])

        evidence = self.adapter.list_successful_login_audit_evidence(
            timestamp_to=self.timestamp_to
        )

        self.assertEqual([item.entry_id for item in evidence], ["newer", "alpha", "zeta"])

    def test_rejects_oversized_content_length_and_chunked_body(self):
        self._respond_with([], content_length=MAX_PROVIDER_AUDIT_RESPONSE_BYTES)
        self.assertEqual(self.adapter.list_successful_login_audit_evidence(timestamp_to=self.timestamp_to), [])
        for payload, content_length in (([], MAX_PROVIDER_AUDIT_RESPONSE_BYTES + 1), (b"x" * (MAX_PROVIDER_AUDIT_RESPONSE_BYTES + 1), None)):
            self._respond_with(payload, content_length=content_length)
            with self.assertRaises(ProviderUnavailable):
                self.adapter.list_successful_login_audit_evidence(timestamp_to=self.timestamp_to)

    def test_rejects_malformed_truncated_or_invalid_required_body(self):
        for payload in (b"[", {}, [{"id": "", "created_at": "2026-08-09T11:00:00Z", "payload": {"action": "login"}}]):
            self._respond_with(payload)
            with self.assertRaises(ProviderUnavailable):
                self.adapter.list_successful_login_audit_evidence(timestamp_to=self.timestamp_to)
        self._respond_with([], status_code=503)
        with self.assertRaises(ProviderUnavailable):
            self.adapter.list_successful_login_audit_evidence(timestamp_to=self.timestamp_to)

    def test_rejects_501_entries_and_duplicate_non_empty_ids(self):
        self._respond_with([self._entry(str(index)) for index in range(501)])
        with self.assertRaises(ProviderUnavailable):
            self.adapter.list_successful_login_audit_evidence(timestamp_to=self.timestamp_to)
        self._respond_with([self._entry("duplicate"), self._entry("duplicate")])
        with self.assertRaises(ProviderUnavailable):
            self.adapter.list_successful_login_audit_evidence(timestamp_to=self.timestamp_to)


if __name__ == "__main__":
    unittest.main()
