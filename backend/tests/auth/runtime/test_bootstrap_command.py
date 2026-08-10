"""Tests for C2: BootstrapInitialAdministrator command.

Validates:
- Bootstrap creates initial administrator with correct attributes
- Idempotent re-run succeeds without creating duplicates
- display_name is passed correctly through provisioning
"""

import unittest
from datetime import UTC, datetime
from typing import Any, cast

from auth.adapters.bootstrap_command import BootstrapInitialAdministrator
from auth.domain.account import AuthenticationAccount
from auth.domain.email import NormalizedEmail
from auth.ports.audit_repository import AuthAuditEntry
from auth.ports.identity_provider import ProviderIdentity

NOW = datetime(2026, 8, 6, 12, 0, 0, tzinfo=UTC)


class _InMemoryAccountRepo:
    def __init__(self):
        self.accounts: dict[str, AuthenticationAccount] = {}

    def find_by_email(self, email: NormalizedEmail):
        for a in self.accounts.values():
            if a.normalized_email.value == email.value:
                return a
        return None

    def find_by_id(self, account_id):
        return self.accounts.get(account_id)

    def save(self, account):
        self.accounts[account.account_id] = account


class _InMemoryAuditRepo:
    def __init__(self):
        self.entries: list[AuthAuditEntry] = []

    def append(self, entry):
        self.entries.append(entry)

    def list_recent(self, limit=50):
        return self.entries[-limit:]


class _FakeIdentityProvider:
    def __init__(self):
        self.created = []
        self.deleted = []

    def create_user(self, *, email, password):
        self.created.append({"email": email, "password": password})
        return ProviderIdentity(subject=f"prov-{len(self.created)}", email=email)

    def delete_user(self, *, subject):
        self.deleted.append(subject)


class _FakeAccessProvisioning:
    def __init__(self):
        self.calls: list[dict] = []

    def provision_profile(self, **kwargs):
        self.calls.append(kwargs)

    def activate_profile(self, **kw):
        pass

    def deactivate_profile(self, **kw):
        pass

    def would_remove_last_administrator(self, subject):
        return False


class _FakeClock:
    def now(self):
        return NOW


class _FakeIdentity:
    def __init__(self):
        self._counter = 0

    def generate_id(self):
        self._counter += 1
        return f"id-{self._counter:04d}"

    def generate_operation_id(self):
        self._counter += 1
        return f"op-{self._counter:04d}"


class TestBootstrapInitialAdministrator(unittest.TestCase):
    def _build(self):
        accounts = _InMemoryAccountRepo()
        audits = _InMemoryAuditRepo()
        provider = _FakeIdentityProvider()
        access = _FakeAccessProvisioning()
        clock = _FakeClock()
        identity = _FakeIdentity()

        command = BootstrapInitialAdministrator(
            account_repository=cast(Any, accounts),
            audit_repository=cast(Any, audits),
            identity_provider=cast(Any, provider),
            access_provisioning=access,
            clock=clock,
            identity=identity,
        )
        return command, accounts, audits, provider, access

    def test_creates_initial_administrator(self):
        command, accounts, audits, provider, access = self._build()

        account_id = command.execute(
            email="admin@example.com",
            provisional_password="temp123",
            user_code="USR-001",
            display_name="System Admin",
        )

        self.assertIsNotNone(account_id)
        self.assertEqual(len(accounts.accounts), 1)
        account = next(iter(accounts.accounts.values()))
        self.assertEqual(account.normalized_email.value, "admin@example.com")
        self.assertEqual(account.display_name, "System Admin")
        self.assertEqual(account.user_code, "USR-001")
        self.assertEqual(account.status.value, "awaiting_password_change")

        # Provider identity created
        self.assertEqual(len(provider.created), 1)

        # Access provisioning called with correct display_name
        self.assertEqual(len(access.calls), 1)
        self.assertEqual(access.calls[0]["display_name"], "System Admin")
        self.assertEqual(access.calls[0]["role_codes"], ["system_administrator"])

        # Audit written
        self.assertEqual(len(audits.entries), 1)
        self.assertEqual(audits.entries[0].event_type, "initial_bootstrap")

    def test_idempotent_rerun_returns_existing(self):
        command, accounts, audits, provider, _access = self._build()

        # First run
        account_id_1 = command.execute(
            email="admin@example.com",
            provisional_password="temp123",
            user_code="USR-001",
            display_name="System Admin",
        )

        # Second run with same email
        account_id_2 = command.execute(
            email="admin@example.com",
            provisional_password="different",
            user_code="USR-001",
            display_name="System Admin",
        )

        self.assertEqual(account_id_1, account_id_2)
        # Only one provider identity created
        self.assertEqual(len(provider.created), 1)
        # Only one account exists
        self.assertEqual(len(accounts.accounts), 1)
        # Only one audit entry
        self.assertEqual(len(audits.entries), 1)

    def test_passes_display_name_through_provisioning(self):
        """C4: display_name is passed to access provisioning, not profile_code."""
        command, _, _, _, access = self._build()

        command.execute(
            email="maria@example.com",
            provisional_password="temp123",
            user_code="USR-015",
            display_name="María García",
        )

        self.assertEqual(access.calls[0]["display_name"], "María García")
        # profile_code is the user_code, not the display_name
        self.assertEqual(access.calls[0]["profile_code"], "USR-015")


if __name__ == "__main__":
    unittest.main()
