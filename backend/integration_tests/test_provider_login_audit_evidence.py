"""Local-only bounded provider audit snapshot proof."""

import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from auth.adapters.identity_provider.admin_client import IdentityProviderAdapter
from auth.application.list_audits import ListAudits
from auth.domain.account import AuthenticationAccount
from auth.domain.email import NormalizedEmail
from auth.ports.audit_repository import AuthAuditEntry
from infra.configuration import ApplicationSettings
from sqlalchemy.orm import Session

from backend.integration_tests.database_test_support import (
    test_engine,
    validated_test_database_url,
)
from supabase import create_client


class ProviderLoginAuditEvidenceIntegrationTests(unittest.TestCase):
    """Exercise a local successful login without claiming provider history."""

    @classmethod
    def setUpClass(cls):
        validated_test_database_url()
        settings = ApplicationSettings.from_environment(Path("backend/.env"))
        assert settings.auth_provider is not None
        cls.url = settings.auth_provider.url
        cls.service_role_key = settings.auth_provider.service_role_key.get_secret_value()
        cls.engine = test_engine()

    def test_available_successful_login_is_safely_mapped_when_visible(self):
        email = f"snapshot-{uuid4().hex}@example.invalid"
        password = "SyntheticSnapshotPass1!"
        database_session = Session(self.engine)
        adapter = IdentityProviderAdapter(
            create_client(self.url, self.service_role_key), database_session
        )
        identity = adapter.create_user(email=email, password=password)
        try:
            login_client = create_client(self.url, self.service_role_key)
            login_client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            evidence = adapter.list_successful_login_audit_evidence(
                timestamp_to=datetime.now(UTC).isoformat().replace("+00:00", "Z")
            )
            matches = [item for item in evidence if item.subject == identity.subject]
            self.assertLessEqual(len(matches), 1)
            as_of = datetime.now(UTC) + timedelta(seconds=1)
            occurred_at = matches[0].occurred_at if matches else as_of.isoformat()
            app_entry = AuthAuditEntry("app-entry", "op", "logout", "succeeded", None, None, None, None, {}, occurred_at)

            class AuditRepository:
                def append(self, entry: AuthAuditEntry) -> None:
                    pass

                def list_by_account(self, account_id: str) -> list[AuthAuditEntry]:
                    return []

                def list_recent(self, limit: int = 50) -> list[AuthAuditEntry]:
                    return []

                def list_keyset(
                    self,
                    *,
                    as_of: str,
                    cursor: tuple[str, str] | None,
                    limit: int,
                ) -> list[AuthAuditEntry]:
                    return [app_entry]

            class AccountRepository:
                def find_by_subject(self, identity_subject: str) -> AuthenticationAccount | None:
                    if identity_subject != identity.subject:
                        return None
                    return AuthenticationAccount.provision(
                        account_id="safe-account",
                        identity_subject=identity_subject,
                        email=NormalizedEmail.from_raw("safe@example.invalid"),
                        display_name="Safe Account",
                        user_code="SAFE-001",
                        now=as_of,
                    )

                def find_by_email(
                    self, email: NormalizedEmail
                ) -> AuthenticationAccount | None:
                    return None

                def find_by_id(self, account_id: str) -> AuthenticationAccount | None:
                    return None

                def list_all(self) -> list[AuthenticationAccount]:
                    return []

                def list_enabled_administrators(self) -> list[AuthenticationAccount]:
                    return []

                def save(self, account: AuthenticationAccount) -> None:
                    pass

            class Clock:
                def now(self) -> datetime:
                    return as_of

            page = ListAudits(AuditRepository(), AccountRepository(), adapter, Clock()).execute()
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
            adapter.delete_user(subject=identity.subject)
            database_session.rollback()
            database_session.close()


if __name__ == "__main__":
    unittest.main()
