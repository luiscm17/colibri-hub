"""Unit tests for Authentication application use cases with test doubles."""

import unittest
from datetime import UTC, datetime
from typing import cast

from auth.application.change_required_password import ChangeRequiredPassword
from auth.application.commands import (
    ChangePasswordCommand,
    DisableAccountCommand,
    EnableAccountCommand,
    ProvisionAccountCommand,
    ResetPasswordCommand,
)
from auth.application.disable_account import DisableAccount
from auth.application.enable_account import EnableAccount
from auth.application.get_current_authentication import GetCurrentAuthentication
from auth.application.list_accounts import ListAccounts
from auth.application.list_audits import ListAudits
from auth.application.provision_account import ProvisionAccount
from auth.application.record_logout import RecordLogout
from auth.application.reset_password import ResetPassword
from auth.domain.account import AuthenticationAccount
from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.email import NormalizedEmail
from auth.domain.errors import (
    AccountNotFound,
    AccountStateConflict,
    DuplicateEmail,
    LastSystemAdministratorRequired,
    ReplacementPasswordMustDiffer,
    VersionConflict,
)
from auth.ports.audit_repository import AuthAuditEntry
from auth.ports.identity_provider import ProviderIdentity, ProviderLoginAuditEvidence

# ─── Test Doubles ───────────────────────────────────────────────────────────────


class InMemoryAccountRepository:
    def __init__(self):
        self.accounts: dict[str, AuthenticationAccount] = {}

    def find_by_subject(self, identity_subject: str):
        for a in self.accounts.values():
            if a.identity_subject == identity_subject:
                return a
        return None

    def find_by_email(self, email: NormalizedEmail):
        for a in self.accounts.values():
            if a.normalized_email.value == email.value:
                return a
        return None

    def find_by_id(self, account_id: str):
        return self.accounts.get(account_id)

    def list_all(self):
        return list(self.accounts.values())

    def list_enabled_administrators(self):
        return [a for a in self.accounts.values() if a.is_enabled]

    def save(self, account: AuthenticationAccount):
        self.accounts[account.account_id] = account


class InMemoryAuditRepository:
    def __init__(self):
        self.entries: list[AuthAuditEntry] = []

    def append(self, entry: AuthAuditEntry):
        self.entries.append(entry)

    def list_by_account(self, account_id: str):
        return [e for e in self.entries if e.affected_account_id == account_id]

    def list_recent(self, limit: int = 50):
        return self.entries[-limit:]

    def list_keyset(self, *, as_of, cursor, limit):
        return self.entries[:limit]


class FakeIdentityProvider:
    def __init__(self):
        self.created_users: list[dict] = []
        self.password_updates: list[dict] = []
        self.banned: set[str] = set()
        self.unbanned: set[str] = set()
        self.revoked: set[str] = set()
        self.deleted: set[str] = set()
        self._next_subject = "provider-sub-001"

    def create_user(self, *, email: str, password: str) -> ProviderIdentity:
        self.created_users.append({"email": email})
        result = ProviderIdentity(subject=self._next_subject, email=email)
        return result

    def update_password(self, *, subject: str, new_password: str):
        self.password_updates.append({"subject": subject})

    def ban_user(self, *, subject: str):
        self.banned.add(subject)

    def unban_user(self, *, subject: str):
        self.unbanned.add(subject)

    def revoke_sessions(self, *, subject: str):
        self.revoked.add(subject)

    def get_session(self, *, session_id: str):
        return None

    def delete_user(self, *, subject: str):
        self.deleted.add(subject)

    def list_successful_login_audit_evidence(self, *, timestamp_to: str):
        return []


class FakeAccessProvisioning:
    def __init__(self, *, would_remove_last: bool = False):
        self.provisioned: list[dict] = []
        self.activated: list[str] = []
        self.deactivated: list[str] = []
        self._would_remove_last = would_remove_last

    def provision_profile(self, *, subject, profile_code, display_name="", role_codes, actor_subject, reason, operation_id):
        self.provisioned.append({"subject": subject, "role_codes": role_codes, "display_name": display_name})

    def activate_profile(self, *, subject, actor_subject, reason, operation_id):
        self.activated.append(subject)

    def deactivate_profile(self, *, subject, actor_subject, reason, operation_id):
        self.deactivated.append(subject)

    def would_remove_last_administrator(self, subject: str) -> bool:
        return self._would_remove_last


class FakeClock:
    def __init__(self, fixed: datetime | None = None):
        self._now = fixed or datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now


class FakeIdentity:
    def __init__(self):
        self._counter = 0

    def generate_id(self) -> str:
        self._counter += 1
        return f"id-{self._counter:03d}"

    def generate_operation_id(self) -> str:
        self._counter += 1
        return f"op-{self._counter:03d}"


# ─── Test Cases ─────────────────────────────────────────────────────────────────


class TestGetCurrentAuthentication(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAccountRepository()
        self.use_case = GetCurrentAuthentication(self.repo)

    def test_returns_change_password_for_awaiting(self):
        account = AuthenticationAccount.provision(
            account_id="acc-1", identity_subject="sub-1",
            email=NormalizedEmail.from_raw("u@e.com"), display_name="U",
            user_code="USR-1", now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.repo.save(account)
        result = self.use_case.execute("sub-1")
        self.assertEqual(result.next_step, "change_password")
        self.assertEqual(result.status, "awaiting_password_change")

    def test_returns_load_access_for_active(self):
        account = AuthenticationAccount.provision(
            account_id="acc-1", identity_subject="sub-1",
            email=NormalizedEmail.from_raw("u@e.com"), display_name="U",
            user_code="USR-1", now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        account.activate(datetime(2026, 1, 2, tzinfo=UTC))
        self.repo.save(account)
        result = self.use_case.execute("sub-1")
        self.assertEqual(result.next_step, "load_access")

    def test_raises_account_not_found(self):
        with self.assertRaises(AccountNotFound):
            self.use_case.execute("nonexistent")


class TestChangeRequiredPassword(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAccountRepository()
        self.audits = InMemoryAuditRepository()
        self.provider = FakeIdentityProvider()
        self.clock = FakeClock()
        self.identity = FakeIdentity()
        self.use_case = ChangeRequiredPassword(
            account_repository=self.repo,
            audit_repository=self.audits,
            identity_provider=self.provider,
            clock=self.clock,
            identity=self.identity,
        )
        self.account = AuthenticationAccount.provision(
            account_id="acc-1", identity_subject="sub-1",
            email=NormalizedEmail.from_raw("u@e.com"), display_name="U",
            user_code="USR-1", now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.repo.save(self.account)

    def test_activates_account_after_password_change(self):
        cmd = ChangePasswordCommand(
            current_password="provisional", new_password="replacement",
            actor_subject="sub-1", session_id="ses-1",
        )
        self.use_case.execute(cmd)
        saved = self.repo.find_by_subject("sub-1")
        assert saved is not None
        self.assertEqual(saved.status, AuthenticationAccountStatus.ACTIVE)

    def test_rejects_same_password(self):
        cmd = ChangePasswordCommand(
            current_password="same", new_password="same",
            actor_subject="sub-1", session_id=None,
        )
        with self.assertRaises(ReplacementPasswordMustDiffer):
            self.use_case.execute(cmd)

    def test_rejects_non_awaiting_account(self):
        self.account.activate(datetime(2026, 1, 2, tzinfo=UTC))
        self.repo.save(self.account)
        cmd = ChangePasswordCommand(
            current_password="old", new_password="new",
            actor_subject="sub-1", session_id=None,
        )
        with self.assertRaises(AccountStateConflict):
            self.use_case.execute(cmd)

    def test_updates_provider_password(self):
        cmd = ChangePasswordCommand(
            current_password="provisional", new_password="replacement",
            actor_subject="sub-1", session_id=None,
        )
        self.use_case.execute(cmd)
        self.assertEqual(len(self.provider.password_updates), 1)

    def test_records_audit_without_secrets(self):
        cmd = ChangePasswordCommand(
            current_password="provisional", new_password="replacement",
            actor_subject="sub-1", session_id="ses-1",
        )
        self.use_case.execute(cmd)
        self.assertEqual(len(self.audits.entries), 1)
        entry = self.audits.entries[0]
        self.assertEqual(entry.event_type, "password_changed")
        # Secrets must never appear in audit details
        self.assertNotIn("provisional", str(entry.details))
        self.assertNotIn("replacement", str(entry.details))


class TestProvisionAccount(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAccountRepository()
        self.audits = InMemoryAuditRepository()
        self.provider = FakeIdentityProvider()
        self.access = FakeAccessProvisioning()
        self.clock = FakeClock()
        self.identity = FakeIdentity()
        self.use_case = ProvisionAccount(
            account_repository=self.repo,
            audit_repository=self.audits,
            identity_provider=self.provider,
            access_provisioning=self.access,
            clock=self.clock,
            identity=self.identity,
        )

    def test_provisions_successfully(self):
        cmd = ProvisionAccountCommand(
            email="new@example.com", provisional_password="temp123",
            user_code="USR-002", display_name="New Person",
            role_codes=["operator"], reason="Assign operator role",
            actor_subject="admin-sub",
        )
        result = self.use_case.execute(cmd)
        self.assertEqual(result.status, "awaiting_password_change")
        self.assertEqual(result.email, "new@example.com")
        self.assertEqual(len(self.access.provisioned), 1)
        self.assertEqual(self.access.provisioned[0]["role_codes"], ["operator"])

    def test_rejects_duplicate_email(self):
        existing = AuthenticationAccount.provision(
            account_id="acc-existing", identity_subject="sub-existing",
            email=NormalizedEmail.from_raw("dup@example.com"),
            display_name="Existing", user_code="USR-001",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.repo.save(existing)
        cmd = ProvisionAccountCommand(
            email="DUP@example.com", provisional_password="temp",
            user_code="USR-003", display_name="Dup",
            role_codes=["r1"], reason="test", actor_subject="admin",
        )
        with self.assertRaises(DuplicateEmail):
            self.use_case.execute(cmd)

    def test_compensates_on_app_failure(self):
        # Make save raise to simulate app persistence failure
        def failing_save(account):
            raise RuntimeError("DB failure")

        self.repo.save = failing_save

        cmd = ProvisionAccountCommand(
            email="fail@example.com", provisional_password="temp",
            user_code="USR-004", display_name="Fail",
            role_codes=["r1"], reason="test", actor_subject="admin",
        )
        with self.assertRaises(RuntimeError):
            self.use_case.execute(cmd)
        # Provider identity should be deleted as compensation
        self.assertIn("provider-sub-001", self.provider.deleted)

    def test_audit_does_not_contain_password(self):
        cmd = ProvisionAccountCommand(
            email="audit@example.com", provisional_password="secret123",
            user_code="USR-005", display_name="Audit Test",
            role_codes=["r1"], reason="test", actor_subject="admin",
        )
        self.use_case.execute(cmd)
        self.assertEqual(len(self.audits.entries), 1)
        entry = self.audits.entries[0]
        self.assertNotIn("secret123", str(entry.details))
        self.assertNotIn("provisional_password", str(entry.details))


class TestResetPassword(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAccountRepository()
        self.audits = InMemoryAuditRepository()
        self.provider = FakeIdentityProvider()
        self.access = FakeAccessProvisioning()
        self.clock = FakeClock()
        self.identity = FakeIdentity()
        self.use_case = ResetPassword(
            account_repository=self.repo,
            audit_repository=self.audits,
            identity_provider=self.provider,
            access_provisioning=self.access,
            clock=self.clock,
            identity=self.identity,
        )
        self.account = AuthenticationAccount.provision(
            account_id="acc-1", identity_subject="sub-1",
            email=NormalizedEmail.from_raw("u@e.com"), display_name="U",
            user_code="USR-1", now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.account.activate(datetime(2026, 1, 2, tzinfo=UTC))
        self.repo.save(self.account)

    def test_resets_to_awaiting(self):
        cmd = ResetPasswordCommand(
            account_id="acc-1", provisional_password="newtemp",
            reason="Forgot", expected_version=2, actor_subject="admin-sub",
        )
        self.use_case.execute(cmd)
        saved = self.repo.find_by_id("acc-1")
        assert saved is not None
        self.assertEqual(saved.status, AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)

    def test_rejects_stale_version(self):
        cmd = ResetPasswordCommand(
            account_id="acc-1", provisional_password="newtemp",
            reason="Forgot", expected_version=99, actor_subject="admin-sub",
        )
        with self.assertRaises(VersionConflict):
            self.use_case.execute(cmd)

    def test_rejects_last_admin_removal(self):
        self.access._would_remove_last = True
        cmd = ResetPasswordCommand(
            account_id="acc-1", provisional_password="newtemp",
            reason="Forgot", expected_version=2, actor_subject="admin-sub",
        )
        with self.assertRaises(LastSystemAdministratorRequired):
            self.use_case.execute(cmd)

    def test_revokes_provider_sessions(self):
        cmd = ResetPasswordCommand(
            account_id="acc-1", provisional_password="newtemp",
            reason="Forgot", expected_version=2, actor_subject="admin-sub",
        )
        self.use_case.execute(cmd)
        self.assertIn("sub-1", self.provider.revoked)


class TestDisableAccount(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAccountRepository()
        self.audits = InMemoryAuditRepository()
        self.provider = FakeIdentityProvider()
        self.access = FakeAccessProvisioning()
        self.clock = FakeClock()
        self.identity = FakeIdentity()
        self.use_case = DisableAccount(
            account_repository=self.repo,
            audit_repository=self.audits,
            identity_provider=self.provider,
            access_provisioning=self.access,
            clock=self.clock,
            identity=self.identity,
        )
        self.account = AuthenticationAccount.provision(
            account_id="acc-1", identity_subject="sub-1",
            email=NormalizedEmail.from_raw("u@e.com"), display_name="U",
            user_code="USR-1", now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.account.activate(datetime(2026, 1, 2, tzinfo=UTC))
        self.repo.save(self.account)

    def test_disables_account(self):
        cmd = DisableAccountCommand(
            account_id="acc-1", reason="Left org",
            expected_version=2, actor_subject="admin-sub",
        )
        self.use_case.execute(cmd)
        saved = self.repo.find_by_id("acc-1")
        assert saved is not None
        self.assertEqual(saved.status, AuthenticationAccountStatus.DISABLED)

    def test_deactivates_access_profile(self):
        cmd = DisableAccountCommand(
            account_id="acc-1", reason="Left org",
            expected_version=2, actor_subject="admin-sub",
        )
        self.use_case.execute(cmd)
        self.assertIn("sub-1", self.access.deactivated)

    def test_bans_and_revokes_provider(self):
        cmd = DisableAccountCommand(
            account_id="acc-1", reason="Left org",
            expected_version=2, actor_subject="admin-sub",
        )
        self.use_case.execute(cmd)
        self.assertIn("sub-1", self.provider.banned)
        self.assertIn("sub-1", self.provider.revoked)

    def test_rejects_last_admin(self):
        self.access._would_remove_last = True
        cmd = DisableAccountCommand(
            account_id="acc-1", reason="Left org",
            expected_version=2, actor_subject="admin-sub",
        )
        with self.assertRaises(LastSystemAdministratorRequired):
            self.use_case.execute(cmd)


class TestEnableAccount(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAccountRepository()
        self.audits = InMemoryAuditRepository()
        self.provider = FakeIdentityProvider()
        self.access = FakeAccessProvisioning()
        self.clock = FakeClock()
        self.identity = FakeIdentity()
        self.use_case = EnableAccount(
            account_repository=self.repo,
            audit_repository=self.audits,
            identity_provider=self.provider,
            access_provisioning=self.access,
            clock=self.clock,
            identity=self.identity,
        )
        self.account = AuthenticationAccount.provision(
            account_id="acc-1", identity_subject="sub-1",
            email=NormalizedEmail.from_raw("u@e.com"), display_name="U",
            user_code="USR-1", now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.account.activate(datetime(2026, 1, 2, tzinfo=UTC))
        self.account.disable(datetime(2026, 1, 3, tzinfo=UTC))
        self.repo.save(self.account)

    def test_enables_disabled_account(self):
        cmd = EnableAccountCommand(
            account_id="acc-1", provisional_password="newtemp",
            reason="Restored", expected_version=3, actor_subject="admin-sub",
        )
        self.use_case.execute(cmd)
        saved = self.repo.find_by_id("acc-1")
        assert saved is not None
        self.assertEqual(saved.status, AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)

    def test_activates_access_profile(self):
        cmd = EnableAccountCommand(
            account_id="acc-1", provisional_password="newtemp",
            reason="Restored", expected_version=3, actor_subject="admin-sub",
        )
        self.use_case.execute(cmd)
        self.assertIn("sub-1", self.access.activated)

    def test_unbans_provider(self):
        cmd = EnableAccountCommand(
            account_id="acc-1", provisional_password="newtemp",
            reason="Restored", expected_version=3, actor_subject="admin-sub",
        )
        self.use_case.execute(cmd)
        self.assertIn("sub-1", self.provider.unbanned)

    def test_rejects_stale_version(self):
        cmd = EnableAccountCommand(
            account_id="acc-1", provisional_password="newtemp",
            reason="Restored", expected_version=1, actor_subject="admin-sub",
        )
        with self.assertRaises(VersionConflict):
            self.use_case.execute(cmd)


class TestRecordLogout(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAccountRepository()
        self.audits = InMemoryAuditRepository()
        self.provider = FakeIdentityProvider()
        self.clock = FakeClock()
        self.identity = FakeIdentity()
        self.use_case = RecordLogout(
            account_repository=self.repo,
            audit_repository=self.audits,
            identity_provider=self.provider,
            clock=self.clock,
            identity=self.identity,
        )
        self.account = AuthenticationAccount.provision(
            account_id="acc-1", identity_subject="sub-1",
            email=NormalizedEmail.from_raw("u@e.com"), display_name="U",
            user_code="USR-1", now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.repo.save(self.account)

    def test_records_logout_and_revokes(self):
        self.use_case.execute(identity_subject="sub-1", session_id="ses-1")
        self.assertIn("sub-1", self.provider.revoked)
        self.assertEqual(len(self.audits.entries), 1)
        self.assertEqual(self.audits.entries[0].event_type, "logout")

    def test_raises_for_unknown_subject(self):
        with self.assertRaises(AccountNotFound):
            self.use_case.execute(identity_subject="unknown", session_id=None)


class TestListAccounts(unittest.TestCase):
    def test_returns_all_accounts(self):
        repo = InMemoryAccountRepository()
        for i in range(3):
            a = AuthenticationAccount.provision(
                account_id=f"acc-{i}", identity_subject=f"sub-{i}",
                email=NormalizedEmail.from_raw(f"u{i}@e.com"),
                display_name=f"User {i}", user_code=f"USR-{i}",
                now=datetime(2026, 1, 1, tzinfo=UTC),
            )
            repo.save(a)
        use_case = ListAccounts(repo)
        result = use_case.execute()
        self.assertEqual(len(result), 3)


class TestListAudits(unittest.TestCase):
    def test_rejects_missing_audit_timestamp_at_the_dto_boundary(self):
        with self.assertRaises(ValueError):
            AuthAuditEntry(
                "audit-1", "operation-1", "logout", "succeeded", None, None,
                None, None, {}, cast(str, None),
            )

    def test_merges_uuid_subjects_and_leaves_unsafe_subjects_uncorrelated(self):
        accounts = InMemoryAccountRepository()
        account = AuthenticationAccount.provision(
            account_id="acc-1", identity_subject="123e4567-e89b-12d3-a456-426614174000",
            email=NormalizedEmail.from_raw("a@example.com"), display_name="A", user_code="A",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        accounts.save(account)
        audits = InMemoryAuditRepository()
        provider = FakeIdentityProvider()
        provider.list_successful_login_audit_evidence = lambda **_: [
            ProviderLoginAuditEvidence("p-unsafe", "2026-08-03T12:00:00+00:00", "email@example.com", "login_succeeded"),
            ProviderLoginAuditEvidence("p-safe", "2026-08-03T12:00:00+00:00", account.identity_subject, "login_succeeded"),
        ]
        page = ListAudits(audits, accounts, provider, FakeClock()).execute()
        self.assertEqual([entry.audit_id for entry in page.entries], ["p-safe", "p-unsafe"])
        self.assertEqual(page.entries[0].affected_account_id, "acc-1")
        self.assertIsNone(page.entries[1].affected_account_id)


if __name__ == "__main__":
    unittest.main()
