"""Unit tests for IdentityProviderAdapter (admin_client.py).

Validates that each adapter method calls the correct Supabase client
methods with the correct arguments and translates errors to domain types.
"""

import unittest
from unittest.mock import MagicMock, patch

from auth.adapters.identity_provider.admin_client import IdentityProviderAdapter
from auth.domain.errors import DuplicateEmail, ProviderUnavailable, WeakPassword


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


if __name__ == "__main__":
    unittest.main()
