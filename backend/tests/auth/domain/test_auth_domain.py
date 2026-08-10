"""Unit tests for Authentication domain: account transitions, email VO, and errors."""

import unittest
from datetime import datetime, timezone

from auth.domain.account import AuthenticationAccount
from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.email import InvalidEmailError, NormalizedEmail
from auth.domain.errors import AccountStateConflict


class TestNormalizedEmail(unittest.TestCase):
    """Email value object: case-folding, validation, immutability."""

    def test_normalizes_to_lowercase(self):
        email = NormalizedEmail.from_raw("User@Example.COM")
        self.assertEqual(email.value, "user@example.com")

    def test_strips_whitespace(self):
        email = NormalizedEmail.from_raw("  user@example.com  ")
        self.assertEqual(email.value, "user@example.com")

    def test_rejects_empty_string(self):
        with self.assertRaises(InvalidEmailError):
            NormalizedEmail.from_raw("")

    def test_rejects_missing_at_sign(self):
        with self.assertRaises(InvalidEmailError):
            NormalizedEmail.from_raw("userexample.com")

    def test_rejects_missing_domain(self):
        with self.assertRaises(InvalidEmailError):
            NormalizedEmail.from_raw("user@")

    def test_valid_organizational_email(self):
        email = NormalizedEmail.from_raw("admin.user@colibri.example")
        self.assertEqual(email.value, "admin.user@colibri.example")

    def test_frozen_immutability(self):
        email = NormalizedEmail.from_raw("user@example.com")
        with self.assertRaises(AttributeError):
            email.value = "other@example.com"  # type: ignore[misc]


class TestAuthenticationAccount(unittest.TestCase):
    """Account entity: transitions, immutability, and version management."""

    def _make_account(
        self, status: AuthenticationAccountStatus = AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE
    ) -> AuthenticationAccount:
        return AuthenticationAccount(
            account_id="acc-001",
            identity_subject="sub-001",
            normalized_email=NormalizedEmail.from_raw("user@example.com"),
            status=status,
            display_name="Test User",
            user_code="USR-001",
            version=1,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

    def test_provision_creates_awaiting_account(self):
        now = datetime(2026, 8, 1, tzinfo=timezone.utc)
        account = AuthenticationAccount.provision(
            account_id="acc-100",
            identity_subject="sub-100",
            email=NormalizedEmail.from_raw("new@example.com"),
            display_name="New User",
            user_code="USR-100",
            now=now,
        )
        self.assertEqual(account.status, AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)
        self.assertEqual(account.version, 1)
        self.assertEqual(account.created_at, now)

    def test_activate_from_awaiting(self):
        account = self._make_account(AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)
        now = datetime(2026, 8, 2, tzinfo=timezone.utc)
        account.activate(now)
        self.assertEqual(account.status, AuthenticationAccountStatus.ACTIVE)
        self.assertEqual(account.version, 2)
        self.assertEqual(account.updated_at, now)

    def test_activate_from_active_raises(self):
        account = self._make_account(AuthenticationAccountStatus.ACTIVE)
        with self.assertRaises(AccountStateConflict) as ctx:
            account.activate(datetime.now(timezone.utc))
        self.assertEqual(ctx.exception.current_status, "active")
        self.assertEqual(ctx.exception.attempted_action, "activate")

    def test_activate_from_disabled_raises(self):
        account = self._make_account(AuthenticationAccountStatus.DISABLED)
        with self.assertRaises(AccountStateConflict):
            account.activate(datetime.now(timezone.utc))

    def test_disable_from_active(self):
        account = self._make_account(AuthenticationAccountStatus.ACTIVE)
        account.disable(datetime(2026, 8, 3, tzinfo=timezone.utc))
        self.assertEqual(account.status, AuthenticationAccountStatus.DISABLED)
        self.assertEqual(account.version, 2)

    def test_disable_from_awaiting(self):
        account = self._make_account(AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)
        account.disable(datetime(2026, 8, 3, tzinfo=timezone.utc))
        self.assertEqual(account.status, AuthenticationAccountStatus.DISABLED)

    def test_disable_from_disabled_raises(self):
        account = self._make_account(AuthenticationAccountStatus.DISABLED)
        with self.assertRaises(AccountStateConflict):
            account.disable(datetime.now(timezone.utc))

    def test_reset_to_awaiting_from_active(self):
        account = self._make_account(AuthenticationAccountStatus.ACTIVE)
        account.reset_to_awaiting(datetime(2026, 8, 4, tzinfo=timezone.utc))
        self.assertEqual(account.status, AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)
        self.assertEqual(account.version, 2)

    def test_reset_from_awaiting_raises(self):
        account = self._make_account(AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)
        with self.assertRaises(AccountStateConflict):
            account.reset_to_awaiting(datetime.now(timezone.utc))

    def test_reset_from_disabled_raises(self):
        account = self._make_account(AuthenticationAccountStatus.DISABLED)
        with self.assertRaises(AccountStateConflict):
            account.reset_to_awaiting(datetime.now(timezone.utc))

    def test_enable_from_disabled(self):
        account = self._make_account(AuthenticationAccountStatus.DISABLED)
        account.enable(datetime(2026, 8, 5, tzinfo=timezone.utc))
        self.assertEqual(account.status, AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)
        self.assertEqual(account.version, 2)

    def test_enable_from_active_raises(self):
        account = self._make_account(AuthenticationAccountStatus.ACTIVE)
        with self.assertRaises(AccountStateConflict):
            account.enable(datetime.now(timezone.utc))

    def test_enable_from_awaiting_raises(self):
        account = self._make_account(AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)
        with self.assertRaises(AccountStateConflict):
            account.enable(datetime.now(timezone.utc))

    def test_is_enabled_property(self):
        active = self._make_account(AuthenticationAccountStatus.ACTIVE)
        awaiting = self._make_account(AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)
        disabled = self._make_account(AuthenticationAccountStatus.DISABLED)
        self.assertTrue(active.is_enabled)
        self.assertTrue(awaiting.is_enabled)
        self.assertFalse(disabled.is_enabled)

    def test_requires_password_change_property(self):
        awaiting = self._make_account(AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)
        active = self._make_account(AuthenticationAccountStatus.ACTIVE)
        self.assertTrue(awaiting.requires_password_change)
        self.assertFalse(active.requires_password_change)

    def test_check_version_matches(self):
        account = self._make_account()
        self.assertTrue(account.check_version(1))
        self.assertFalse(account.check_version(2))


if __name__ == "__main__":
    unittest.main()
