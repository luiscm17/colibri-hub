"""Unit tests for Authentication request pipeline."""

import unittest
from datetime import UTC, datetime, timedelta

from auth.adapters.identity_provider.request_pipeline import RequestPipeline
from auth.domain.account import AuthenticationAccount
from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.email import NormalizedEmail
from auth.domain.errors import (
    AuthenticationFailed,
    AuthenticationRequired,
    PasswordChangeRequired,
)
from auth.ports.identity_provider import ProviderIdentity, ProviderSession
from shared.identity import AuthenticatedIdentity

# ─── Test Doubles ───────────────────────────────────────────────────────────────


class FakeAccountRepository:
    def __init__(self, accounts: dict[str, AuthenticationAccount] | None = None):
        self._accounts = accounts or {}

    def find_by_subject(self, identity_subject: str):
        return self._accounts.get(identity_subject)

    def find_by_email(self, email): return None
    def find_by_id(self, account_id): return None
    def list_all(self): return []
    def list_enabled_administrators(self): return []
    def save(self, account): pass


class FakeIdentityProvider:
    def __init__(self, sessions: dict[str, ProviderSession] | None = None):
        self._sessions = sessions or {}

    def get_session(self, *, session_id: str):
        return self._sessions.get(session_id)

    def create_user(self, *, email: str, password: str) -> ProviderIdentity:
        del password
        return ProviderIdentity(subject="unused", email=email)
    def update_password(self, **kwargs): pass
    def ban_user(self, **kwargs): pass
    def unban_user(self, **kwargs): pass
    def revoke_sessions(self, **kwargs): pass
    def delete_user(self, **kwargs): pass

    def list_successful_login_audit_evidence(self, *, timestamp_to: str):
        del timestamp_to
        return []


def _make_account(
    subject: str,
    status: AuthenticationAccountStatus = AuthenticationAccountStatus.ACTIVE,
) -> AuthenticationAccount:
    return AuthenticationAccount(
        account_id="acc-1",
        identity_subject=subject,
        normalized_email=NormalizedEmail.from_raw("u@example.com"),
        status=status,
        display_name="Test",
        user_code="USR-1",
        version=1,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


# ─── Test Cases ─────────────────────────────────────────────────────────────────


class TestPipelineAccountState(unittest.TestCase):
    """Pipeline rejects disabled accounts and unknown subjects."""

    def test_unknown_subject_raises_authentication_failed(self):
        pipeline = RequestPipeline(
            account_repository=FakeAccountRepository(),
            identity_provider=FakeIdentityProvider(),
        )
        identity = AuthenticatedIdentity(subject="unknown", session_id=None)
        with self.assertRaises(AuthenticationFailed):
            pipeline.validate(identity, "/api/v1/warehouse/bales", "GET")

    def test_disabled_account_raises_authentication_failed(self):
        account = _make_account("sub-1", AuthenticationAccountStatus.DISABLED)
        pipeline = RequestPipeline(
            account_repository=FakeAccountRepository({"sub-1": account}),
            identity_provider=FakeIdentityProvider(),
        )
        identity = AuthenticatedIdentity(subject="sub-1", session_id=None)
        with self.assertRaises(AuthenticationFailed):
            pipeline.validate(identity, "/api/v1/warehouse/bales", "GET")

    def test_active_account_passes(self):
        account = _make_account("sub-1", AuthenticationAccountStatus.ACTIVE)
        pipeline = RequestPipeline(
            account_repository=FakeAccountRepository({"sub-1": account}),
            identity_provider=FakeIdentityProvider(),
        )
        identity = AuthenticatedIdentity(subject="sub-1", session_id=None)
        result = pipeline.validate(identity, "/api/v1/warehouse/bales", "GET")
        self.assertEqual(result.subject, "sub-1")


class TestPipelineSessionAge(unittest.TestCase):
    """Pipeline rejects sessions older than 8 hours."""

    def test_session_within_8h_passes(self):
        now = datetime.now(UTC)
        session = ProviderSession(
            session_id="ses-1",
            created_at=(now - timedelta(hours=7)).isoformat(),
            is_active=True,
        )
        account = _make_account("sub-1")
        pipeline = RequestPipeline(
            account_repository=FakeAccountRepository({"sub-1": account}),
            identity_provider=FakeIdentityProvider({"ses-1": session}),
        )
        identity = AuthenticatedIdentity(subject="sub-1", session_id="ses-1")
        result = pipeline.validate(identity, "/api/v1/warehouse/bales", "GET")
        self.assertEqual(result.subject, "sub-1")

    def test_session_at_8h_boundary_raises(self):
        now = datetime.now(UTC)
        session = ProviderSession(
            session_id="ses-1",
            created_at=(now - timedelta(hours=8, seconds=1)).isoformat(),
            is_active=True,
        )
        account = _make_account("sub-1")
        pipeline = RequestPipeline(
            account_repository=FakeAccountRepository({"sub-1": account}),
            identity_provider=FakeIdentityProvider({"ses-1": session}),
        )
        identity = AuthenticatedIdentity(subject="sub-1", session_id="ses-1")
        with self.assertRaises(AuthenticationRequired):
            pipeline.validate(identity, "/api/v1/warehouse/bales", "GET")

    def test_ended_session_raises(self):
        session = ProviderSession(
            session_id="ses-1",
            created_at=datetime.now(UTC).isoformat(),
            is_active=False,
        )
        account = _make_account("sub-1")
        pipeline = RequestPipeline(
            account_repository=FakeAccountRepository({"sub-1": account}),
            identity_provider=FakeIdentityProvider({"ses-1": session}),
        )
        identity = AuthenticatedIdentity(subject="sub-1", session_id="ses-1")
        with self.assertRaises(AuthenticationRequired):
            pipeline.validate(identity, "/api/v1/warehouse/bales", "GET")

    def test_missing_session_in_provider_raises(self):
        account = _make_account("sub-1")
        pipeline = RequestPipeline(
            account_repository=FakeAccountRepository({"sub-1": account}),
            identity_provider=FakeIdentityProvider(),  # empty — session not found
        )
        identity = AuthenticatedIdentity(subject="sub-1", session_id="ses-gone")
        with self.assertRaises(AuthenticationRequired):
            pipeline.validate(identity, "/api/v1/warehouse/bales", "GET")


class TestPipelineAwaitingRestriction(unittest.TestCase):
    """Pipeline restricts awaiting_password_change to permitted endpoints."""

    def _make_pipeline(self):
        account = _make_account(
            "sub-1", AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE
        )
        return RequestPipeline(
            account_repository=FakeAccountRepository({"sub-1": account}),
            identity_provider=FakeIdentityProvider(),
        )

    def test_get_auth_me_permitted(self):
        pipeline = self._make_pipeline()
        identity = AuthenticatedIdentity(subject="sub-1", session_id=None)
        result = pipeline.validate(identity, "/api/v1/auth/me", "GET")
        self.assertEqual(result.subject, "sub-1")

    def test_post_password_change_permitted(self):
        pipeline = self._make_pipeline()
        identity = AuthenticatedIdentity(subject="sub-1", session_id=None)
        result = pipeline.validate(identity, "/api/v1/auth/password-change", "POST")
        self.assertEqual(result.subject, "sub-1")

    def test_delete_session_permitted(self):
        pipeline = self._make_pipeline()
        identity = AuthenticatedIdentity(subject="sub-1", session_id=None)
        result = pipeline.validate(identity, "/api/v1/auth/session", "DELETE")
        self.assertEqual(result.subject, "sub-1")

    def test_other_endpoint_raises_password_change_required(self):
        pipeline = self._make_pipeline()
        identity = AuthenticatedIdentity(subject="sub-1", session_id=None)
        with self.assertRaises(PasswordChangeRequired):
            pipeline.validate(identity, "/api/v1/warehouse/bales", "POST")

    def test_get_access_me_raises_password_change_required(self):
        pipeline = self._make_pipeline()
        identity = AuthenticatedIdentity(subject="sub-1", session_id=None)
        with self.assertRaises(PasswordChangeRequired):
            pipeline.validate(identity, "/api/v1/access/me", "GET")


if __name__ == "__main__":
    unittest.main()
