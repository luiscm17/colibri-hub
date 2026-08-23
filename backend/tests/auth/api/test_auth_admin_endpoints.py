"""TestClient tests for Authentication admin HTTP endpoints (disable/enable/reset).

Validates HTTP status codes, error mapping, and request handling for the
administrative account management paths.
"""

import unittest
from datetime import UTC, datetime

from auth.adapters.http.admin_router import create_auth_admin_router
from auth.application.auth_use_cases import AuthUseCases
from auth.application.change_required_password import ChangeRequiredPassword
from auth.application.disable_account import DisableAccount
from auth.application.enable_account import EnableAccount
from auth.application.get_account import GetAccount
from auth.application.get_current_authentication import GetCurrentAuthentication
from auth.application.list_accounts import ListAccounts
from auth.application.list_audits import ListAudits
from auth.application.provision_account import ProvisionAccount
from auth.application.record_logout import RecordLogout
from auth.application.reset_password import ResetPassword
from auth.domain.account import AuthenticationAccount
from auth.domain.email import NormalizedEmail
from auth.domain.errors import ProviderUnavailable
from auth.ports.audit_repository import AuthAuditEntry
from auth.ports.identity_provider import ProviderIdentity
from bootstrap.http_error_handlers import register_exception_handlers
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from shared.identity import AuthenticatedIdentity

# ─── Test Doubles ───────────────────────────────────────────────────────────────


class InMemoryAccountRepository:
    def __init__(self):
        self.accounts: dict[str, AuthenticationAccount] = {}

    def find_by_subject(self, identity_subject):
        for a in self.accounts.values():
            if a.identity_subject == identity_subject:
                return a
        return None

    def find_by_email(self, email):
        for a in self.accounts.values():
            if a.normalized_email.value == email.value:
                return a
        return None

    def find_by_id(self, account_id):
        return self.accounts.get(account_id)

    def list_all(self):
        return list(self.accounts.values())

    def list_enabled_administrators(self):
        return [a for a in self.accounts.values() if a.is_enabled]

    def save(self, account):
        self.accounts[account.account_id] = account


class InMemoryAuditRepository:
    def __init__(self):
        self.entries: list[AuthAuditEntry] = []

    def append(self, entry):
        self.entries.append(entry)

    def list_by_account(self, account_id):
        return [e for e in self.entries if e.affected_account_id == account_id]

    def list_recent(self, limit=50):
        return self.entries[-limit:]

    def list_keyset(self, *, as_of, cursor, limit):
        return self.entries[:limit]


class FakeIdentityProvider:
    def __init__(self, *, ban_raises: bool = False):
        self._ban_raises = ban_raises

    def create_user(self, *, email, password):
        return ProviderIdentity(subject="prov-sub-1", email=email)

    def update_password(self, **kwargs):
        pass

    def ban_user(self, *, subject):
        if self._ban_raises:
            raise ProviderUnavailable()

    def unban_user(self, **kwargs):
        pass

    def revoke_session(self, *, session_id, subject):
        pass

    def revoke_subject_sessions(self, *, subject):
        pass

    def has_active_session(self, *, session_id, subject):
        return False

    def delete_user(self, **kwargs):
        pass

    def list_successful_login_audit_evidence(self, *, timestamp_to):
        if self._ban_raises:
            raise ProviderUnavailable()
        return []


class FakeAccessProvisioning:
    def __init__(self):
        self.provisioned = []

    def provision_profile(self, **kwargs):
        self.provisioned.append(kwargs)

    def activate_profile(self, **kwargs):
        pass

    def deactivate_profile(self, **kwargs):
        pass

    def assert_reduction_allowed(self, subject):
        return None


class FakeTransaction:
    def commit(self):
        pass


class FakeClock:
    def now(self):
        return datetime(2026, 8, 3, 15, 0, 0, tzinfo=UTC)


class FakeIdentity:
    def __init__(self):
        self._counter = 0

    def generate_id(self):
        self._counter += 1
        return f"id-{self._counter:04d}"

    def generate_operation_id(self):
        self._counter += 1
        return f"op-{self._counter:04d}"


# ─── App Factory ────────────────────────────────────────────────────────────────


def _build_test_app(
    *,
    accounts: dict[str, AuthenticationAccount] | None = None,
    provider: FakeIdentityProvider | None = None,
) -> tuple[TestClient, InMemoryAccountRepository]:
    repo = InMemoryAccountRepository()
    if accounts:
        for acc in accounts.values():
            repo.accounts[acc.account_id] = acc

    audits = InMemoryAuditRepository()
    if provider is None:
        provider = FakeIdentityProvider()
    access = FakeAccessProvisioning()
    clock = FakeClock()
    identity = FakeIdentity()
    transaction = FakeTransaction()

    use_cases = AuthUseCases(
        get_current_authentication=GetCurrentAuthentication(repo),
        change_required_password=ChangeRequiredPassword(
            account_repository=repo,
            audit_repository=audits,
            clock=clock,
            identity=identity,
        ),
        record_logout=RecordLogout(
            account_repository=repo,
            audit_repository=audits,
            identity_provider=provider,
            clock=clock,
            identity=identity,
        ),
        provision_account=ProvisionAccount(
            account_repository=repo,
            audit_repository=audits,
            identity_provider=provider,
            access_provisioning=access,
            clock=clock,
            identity=identity,
        ),
        reset_password=ResetPassword(
            account_repository=repo,
            audit_repository=audits,
            identity_provider=provider,
            access_provisioning=access,
            transaction=transaction,
            clock=clock,
            identity=identity,
        ),
        disable_account=DisableAccount(
            account_repository=repo,
            audit_repository=audits,
            identity_provider=provider,
            access_provisioning=access,
            transaction=transaction,
            clock=clock,
            identity=identity,
        ),
        enable_account=EnableAccount(
            account_repository=repo,
            audit_repository=audits,
            identity_provider=provider,
            access_provisioning=access,
            clock=clock,
            identity=identity,
        ),
        get_account=GetAccount(repo),
        list_accounts=ListAccounts(repo),
        list_audits=ListAudits(audits, repo, provider, clock),
    )

    def identity_resolver() -> AuthenticatedIdentity:
        return AuthenticatedIdentity(subject="admin-subject", session_id="ses-test")

    def use_case_factory() -> AuthUseCases:
        return use_cases

    app = FastAPI()
    register_exception_handlers(app)
    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(
        create_auth_admin_router(identity_resolver, use_case_factory)
    )
    app.include_router(api_router)

    return TestClient(app), repo


def _make_active_account(account_id: str = "acc-1") -> AuthenticationAccount:
    """Create an active account for testing."""
    account = AuthenticationAccount.provision(
        account_id=account_id,
        identity_subject="target-subject",
        email=NormalizedEmail.from_raw("target@example.com"),
        display_name="Target User",
        user_code="USR-TARGET",
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    account.activate(datetime(2026, 1, 2, tzinfo=UTC))
    return account


def _make_disabled_account(account_id: str = "acc-1") -> AuthenticationAccount:
    """Create a disabled account for testing."""
    account = _make_active_account(account_id)
    account.disable(datetime(2026, 1, 3, tzinfo=UTC))
    return account


# ─── Disable Tests ──────────────────────────────────────────────────────────────


class TestDisableEndpoint(unittest.TestCase):
    def test_returns_204_on_success(self):
        account = _make_active_account()
        client, _ = _build_test_app(accounts={"acc-1": account})

        response = client.post(
            "/api/v1/auth/accounts/acc-1/disable",
            json={"reason": "Left organization", "expected_version": 2},
        )

        self.assertEqual(response.status_code, 204)

    def test_returns_404_for_nonexistent_account(self):
        client, _ = _build_test_app()

        response = client.post(
            "/api/v1/auth/accounts/nonexistent/disable",
            json={"reason": "Test", "expected_version": 1},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "authentication_account_not_found",
        )

    def test_returns_409_for_version_conflict(self):
        account = _make_active_account()
        client, _ = _build_test_app(accounts={"acc-1": account})

        response = client.post(
            "/api/v1/auth/accounts/acc-1/disable",
            json={"reason": "Test", "expected_version": 99},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "authentication_version_conflict",
        )

    def test_returns_503_when_provider_unavailable(self):
        account = _make_active_account()
        provider = FakeIdentityProvider(ban_raises=True)
        client, repo = _build_test_app(accounts={"acc-1": account}, provider=provider)

        response = client.post(
            "/api/v1/auth/accounts/acc-1/disable",
            json={"reason": "Test", "expected_version": 2},
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["error"]["code"],
            "authentication_provider_unavailable",
        )
        saved = repo.find_by_id("acc-1")
        assert saved is not None
        self.assertEqual(saved.status.value, "disabled")


# ─── Enable Tests ───────────────────────────────────────────────────────────────


class TestEnableEndpoint(unittest.TestCase):
    def test_returns_204_on_success(self):
        account = _make_disabled_account()
        client, _ = _build_test_app(accounts={"acc-1": account})

        response = client.post(
            "/api/v1/auth/accounts/acc-1/enable",
            json={
                "provisional_password": "newtemp123",
                "reason": "Restored",
                "expected_version": 3,
            },
        )

        self.assertEqual(response.status_code, 204)


# ─── Reset Password Tests ──────────────────────────────────────────────────────


class TestResetPasswordEndpoint(unittest.TestCase):
    def test_returns_204_on_success(self):
        account = _make_active_account()
        client, _ = _build_test_app(accounts={"acc-1": account})

        response = client.post(
            "/api/v1/auth/accounts/acc-1/password-reset",
            json={
                "provisional_password": "temppass",
                "reason": "Forgot password",
                "expected_version": 2,
            },
        )

        self.assertEqual(response.status_code, 204)


class TestAuditEndpoint(unittest.TestCase):
    def test_rejects_malformed_cursor(self):
        client, _ = _build_test_app()
        self.assertEqual(
            client.get("/api/v1/auth/audits?cursor=not-a-cursor").status_code, 422
        )

    def test_returns_source_tagged_page(self):
        client, _ = _build_test_app()
        self.assertEqual(
            client.get("/api/v1/auth/audits").json(), {"entries": [], "cursor": None}
        )

    def test_returns_no_partial_page_when_provider_is_unavailable(self):
        client, _ = _build_test_app(provider=FakeIdentityProvider(ban_raises=True))
        response = client.get("/api/v1/auth/audits")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["error"]["code"], "authentication_provider_unavailable"
        )


if __name__ == "__main__":
    unittest.main()
