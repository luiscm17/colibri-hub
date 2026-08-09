"""Local-only bounded provider audit snapshot proof."""

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from supabase import create_client

from auth.adapters.identity_provider.admin_client import IdentityProviderAdapter
from auth.application.list_audits import ListAudits
from auth.ports.audit_repository import AuthAuditEntry
from backend.integration_tests.database_test_support import validated_test_database_url
from infra.configuration import ApplicationSettings


class ProviderLoginAuditEvidenceIntegrationTests(unittest.TestCase):
    """Exercise a local successful login without claiming provider history."""

    @classmethod
    def setUpClass(cls):
        validated_test_database_url()
        settings = ApplicationSettings.from_environment(Path("backend/.env"))
        assert settings.auth_provider is not None
        cls.url = settings.auth_provider.url
        cls.service_role_key = settings.auth_provider.service_role_key.get_secret_value()
        cls.adapter = IdentityProviderAdapter(create_client(cls.url, cls.service_role_key))

    def test_available_successful_login_is_safely_mapped_when_visible(self):
        email = f"snapshot-{uuid4().hex}@example.invalid"
        password = "SyntheticSnapshotPass1!"
        identity = self.adapter.create_user(email=email, password=password)
        try:
            login_client = create_client(self.url, self.service_role_key)
            login_client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            evidence = self.adapter.list_successful_login_audit_evidence(
                timestamp_to=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )
            matches = [item for item in evidence if item.subject == identity.subject]
            self.assertLessEqual(len(matches), 1)
            as_of = datetime.now(timezone.utc) + timedelta(seconds=1)
            occurred_at = matches[0].occurred_at if matches else as_of.isoformat()
            app_entry = AuthAuditEntry("app-entry", "op", "logout", "succeeded", None, None, None, None, {}, occurred_at)

            class AuditRepository:
                def list_keyset(self, **_): return [app_entry]

            class AccountRepository:
                def find_by_subject(self, subject):
                    return type("Account", (), {"account_id": "safe-account"})() if subject == identity.subject else None

            class Clock:
                def now(self): return as_of

            page = ListAudits(AuditRepository(), AccountRepository(), self.adapter, Clock()).execute()
            self.assertIn(app_entry, page.entries)
            if matches:
                provider_entry = next(item for item in page.entries if item.audit_id == matches[0].entry_id)
                self.assertEqual(
                    (provider_entry.source, provider_entry.event_type, provider_entry.affected_account_id),
                    ("provider", "login_succeeded", "safe-account"),
                )
                self.assertEqual((provider_entry.operation_id, provider_entry.actor_identity_subject, provider_entry.provider_session_id, provider_entry.reason, provider_entry.details), ("", None, None, None, {}))
                self.assertEqual([item.audit_id for item in page.entries if item.audit_id in {"app-entry", provider_entry.audit_id}], ["app-entry", provider_entry.audit_id])
            # A zero-visible snapshot is not evidence that provider history is empty.
        finally:
            self.adapter.delete_user(subject=identity.subject)


if __name__ == "__main__":
    unittest.main()
