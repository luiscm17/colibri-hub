"""Tests for C5: login audit events persisted with correct event_type.

Validates that record_login_outcome writes login_succeeded and login_failed
events with the correct structure.
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from auth.adapters.persistence.audit_repository import AuthAuditRepositoryAdapter
from auth.ports.audit_repository import AuthAuditEntry


class TestLoginAuditEvents(unittest.TestCase):
    """C5: login audit events persisted with correct event_type."""

    def _make_adapter(self):
        session = MagicMock()
        adapter = AuthAuditRepositoryAdapter(session)
        return adapter, session

    @patch.object(AuthAuditRepositoryAdapter, "append")
    def test_record_login_succeeded(self, mock_append):
        adapter, _ = self._make_adapter()

        adapter.record_login_outcome(
            audit_id="audit-001",
            operation_id="op-001",
            event_type="login_succeeded",
            outcome="succeeded",
            actor_identity_subject="sub-123",
            affected_account_id="acc-456",
            provider_session_id="sess-789",
            occurred_at="2026-08-06T12:00:00+00:00",
        )

        mock_append.assert_called_once()
        entry = mock_append.call_args[0][0]
        self.assertIsInstance(entry, AuthAuditEntry)
        self.assertEqual(entry.event_type, "login_succeeded")
        self.assertEqual(entry.outcome, "succeeded")
        self.assertEqual(entry.actor_identity_subject, "sub-123")
        self.assertEqual(entry.affected_account_id, "acc-456")
        self.assertEqual(entry.provider_session_id, "sess-789")
        self.assertEqual(entry.audit_id, "audit-001")

    @patch.object(AuthAuditRepositoryAdapter, "append")
    def test_record_login_failed(self, mock_append):
        adapter, _ = self._make_adapter()

        adapter.record_login_outcome(
            audit_id="audit-002",
            operation_id="op-002",
            event_type="login_failed",
            outcome="failed",
            actor_identity_subject=None,
            affected_account_id=None,
            provider_session_id=None,
            occurred_at="2026-08-06T12:01:00+00:00",
        )

        mock_append.assert_called_once()
        entry = mock_append.call_args[0][0]
        self.assertEqual(entry.event_type, "login_failed")
        self.assertEqual(entry.outcome, "failed")
        self.assertIsNone(entry.actor_identity_subject)
        self.assertIsNone(entry.affected_account_id)
        self.assertIsNone(entry.provider_session_id)

    @patch.object(AuthAuditRepositoryAdapter, "append")
    def test_login_event_has_empty_details(self, mock_append):
        """Login events should not reveal account existence info."""
        adapter, _ = self._make_adapter()

        adapter.record_login_outcome(
            audit_id="audit-003",
            operation_id="op-003",
            event_type="login_failed",
            outcome="failed",
            occurred_at="2026-08-06T12:02:00+00:00",
        )

        entry = mock_append.call_args[0][0]
        self.assertEqual(entry.details, {})
        self.assertIsNone(entry.reason)


if __name__ == "__main__":
    unittest.main()
