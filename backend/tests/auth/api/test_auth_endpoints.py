"""TestClient tests for Authentication HTTP endpoints."""

import unittest
from datetime import UTC, datetime

from auth.adapters.http.admin_router import create_auth_admin_router
from auth.adapters.http.user_router import create_auth_user_router
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
from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.email import NormalizedEmail
from auth.domain.errors import CurrentPasswordRejected
from auth.ports.audit_repository import AuthAuditEntry
from auth.ports.identity_provider import ProviderIdentity
from bootstrap.http_error_handlers import register_exception_handlers
from fastapi import FastAPI
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
    def __init__(self):
        self._counter = 0

    def create_user(self, *, email, password):
        self._counter += 1
        return ProviderIdentity(subject=f"prov-sub-{self._counter}", email=email)

    def update_password(self, **kwargs):
        pass

    def ban_user(self, **kwargs):
        pass

    def unban_user(self, **kwargs):
        pass

    def revoke_session(self, *, session_id, subject):
        pass

    def revoke_subject_sessions(self, *, subject):
        pass

    def has_active_session(self, *, session_id, subject):
        return False

    def list_successful_login_audit_evidence(self, *, timestamp_to):
        return []

    def delete_user(self, **kwargs):
        pass


class FakePasswordReplacement:
    def __init__(self, *, reject_current_password: bool = False) -> None:
        self.reject_current_password = reject_current_password

    def replace_required_password(self, **kwargs) -> None:
        if self.reject_current_password:
            raise CurrentPasswordRejected()


class FakeAccessProvisioning:
    def __init__(self):
        self.provisioned = []

    def provision_profile(self, **kwargs):
        self.provisioned.append(kwargs)

    def activate_profile(self, **kwargs):
        pass

    def deactivate_profile(self, **kwargs):
        pass

    def would_remove_last_administrator(self, subject):
        return False


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
    identity_subject: str = "test-subject",
    accounts: dict | None = None,
    session_id: str | None = "ses-test",
    password_replacement: FakePasswordReplacement | None = None,
) -> tuple[TestClient, InMemoryAccountRepository]:
    repo = InMemoryAccountRepository()
    if accounts:
        for acc in accounts.values():
            repo.accounts[acc.account_id] = acc

    audits = InMemoryAuditRepository()
    provider = FakeIdentityProvider()
    password_replacement = password_replacement or FakePasswordReplacement()
    access = FakeAccessProvisioning()
    clock = FakeClock()
    identity = FakeIdentity()
    transaction = FakeTransaction()

    use_cases = AuthUseCases(
        get_current_authentication=GetCurrentAuthentication(repo),
        change_required_password=ChangeRequiredPassword(
            account_repository=repo,
            audit_repository=audits,
            password_replacement=password_replacement,
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
        return AuthenticatedIdentity(
            subject=identity_subject,
            session_id=session_id,
        )

    def use_case_factory() -> AuthUseCases:
        return use_cases

    app = FastAPI()
    register_exception_handlers(app)
    from fastapi import APIRouter

    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(
        create_auth_user_router(identity_resolver, use_case_factory)
    )
    api_router.include_router(
        create_auth_admin_router(identity_resolver, use_case_factory)
    )
    app.include_router(api_router)

    return TestClient(app), repo


# ─── Test Cases ─────────────────────────────────────────────────────────────────


class TestAuthMeEndpoint(unittest.TestCase):
    def test_returns_awaiting_state(self):
        account = AuthenticationAccount.provision(
            account_id="acc-1",
            identity_subject="test-subject",
            email=NormalizedEmail.from_raw("u@e.com"),
            display_name="User",
            user_code="USR-1",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        client, _ = _build_test_app(accounts={"acc-1": account})
        response = client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "awaiting_password_change")
        self.assertEqual(data["next_step"], "change_password")

    def test_returns_active_state(self):
        account = AuthenticationAccount.provision(
            account_id="acc-1",
            identity_subject="test-subject",
            email=NormalizedEmail.from_raw("u@e.com"),
            display_name="User",
            user_code="USR-1",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        account.activate(datetime(2026, 1, 2, tzinfo=UTC))
        client, _ = _build_test_app(accounts={"acc-1": account})
        response = client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["next_step"], "load_access")

    def test_unknown_subject_returns_404(self):
        client, _ = _build_test_app()
        response = client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 404)


class TestPasswordChangeEndpoint(unittest.TestCase):
    def test_successful_change(self):
        account = AuthenticationAccount.provision(
            account_id="acc-1",
            identity_subject="test-subject",
            email=NormalizedEmail.from_raw("u@e.com"),
            display_name="User",
            user_code="USR-1",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        client, repo = _build_test_app(accounts={"acc-1": account})
        response = client.post(
            "/api/v1/auth/password-change",
            json={"current_password": "old", "new_password": "new"},
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        saved = repo.find_by_id("acc-1")
        assert saved is not None
        self.assertEqual(saved.status, AuthenticationAccountStatus.ACTIVE)

    def test_wrong_current_password_returns_safe_401_without_session_response(self):
        account = AuthenticationAccount.provision(
            account_id="acc-1",
            identity_subject="test-subject",
            email=NormalizedEmail.from_raw("u@e.com"),
            display_name="User",
            user_code="USR-1",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        client, repo = _build_test_app(
            accounts={"acc-1": account},
            password_replacement=FakePasswordReplacement(reject_current_password=True),
        )

        response = client.post(
            "/api/v1/auth/password-change",
            json={"current_password": "wrong", "new_password": "replacement"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "current_password_rejected")
        self.assertEqual(response.json()["error"]["message"], "The current password is incorrect.")
        self.assertNotIn("session", response.text)
        self.assertNotIn("token", response.text)
        self.assertNotIn("wrong", response.text)
        saved = repo.find_by_id("acc-1")
        assert saved is not None
        self.assertEqual(saved.status, AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE)

    def test_same_password_returns_422(self):
        account = AuthenticationAccount.provision(
            account_id="acc-1",
            identity_subject="test-subject",
            email=NormalizedEmail.from_raw("u@e.com"),
            display_name="User",
            user_code="USR-1",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        client, _ = _build_test_app(accounts={"acc-1": account})
        response = client.post(
            "/api/v1/auth/password-change",
            json={"current_password": "same", "new_password": "same"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"], "replacement_password_must_differ"
        )


class TestLogoutEndpoint(unittest.TestCase):
    def test_successful_logout(self):
        account = AuthenticationAccount.provision(
            account_id="acc-1",
            identity_subject="test-subject",
            email=NormalizedEmail.from_raw("u@e.com"),
            display_name="User",
            user_code="USR-1",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        client, _ = _build_test_app(accounts={"acc-1": account})
        response = client.delete("/api/v1/auth/session")
        self.assertEqual(response.status_code, 204)

    def test_missing_session_returns_authentication_required(self):
        account = AuthenticationAccount.provision(
            account_id="acc-1",
            identity_subject="test-subject",
            email=NormalizedEmail.from_raw("u@e.com"),
            display_name="User",
            user_code="USR-1",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        client, _ = _build_test_app(
            accounts={
                "acc-1": account,
            },
            session_id=None,
        )

        response = client.delete("/api/v1/auth/session")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "authentication_required",
                    "message": "Authentication is required.",
                    "fields": [],
                }
            },
        )


class TestProvisionEndpoint(unittest.TestCase):
    def test_successful_provision(self):
        # Need an existing account for the admin identity
        admin = AuthenticationAccount.provision(
            account_id="acc-admin",
            identity_subject="test-subject",
            email=NormalizedEmail.from_raw("admin@e.com"),
            display_name="Admin",
            user_code="USR-ADMIN",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        client, _repo = _build_test_app(accounts={"acc-admin": admin})
        response = client.post(
            "/api/v1/auth/accounts",
            json={
                "email": "new@example.com",
                "provisional_password": "temp123",
                "user_code": "USR-NEW",
                "display_name": "New User",
                "role_codes": ["operator"],
                "reason": "New hire",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "awaiting_password_change")
        self.assertEqual(data["email"], "new@example.com")

    def test_duplicate_email_returns_409(self):
        admin = AuthenticationAccount.provision(
            account_id="acc-admin",
            identity_subject="test-subject",
            email=NormalizedEmail.from_raw("existing@e.com"),
            display_name="Admin",
            user_code="USR-ADMIN",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        client, _ = _build_test_app(accounts={"acc-admin": admin})
        response = client.post(
            "/api/v1/auth/accounts",
            json={
                "email": "EXISTING@e.com",
                "provisional_password": "temp",
                "user_code": "USR-DUP",
                "display_name": "Dup",
                "role_codes": ["r1"],
                "reason": "test",
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"], "duplicate_authentication_email"
        )

    def test_response_does_not_contain_password(self):
        admin = AuthenticationAccount.provision(
            account_id="acc-admin",
            identity_subject="test-subject",
            email=NormalizedEmail.from_raw("admin@e.com"),
            display_name="Admin",
            user_code="USR-ADMIN",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        client, _ = _build_test_app(accounts={"acc-admin": admin})
        response = client.post(
            "/api/v1/auth/accounts",
            json={
                "email": "safe@example.com",
                "provisional_password": "secret-value-123",
                "user_code": "USR-SAFE",
                "display_name": "Safe",
                "role_codes": ["r1"],
                "reason": "test",
            },
        )
        self.assertNotIn("secret-value-123", response.text)
        self.assertNotIn("provisional_password", response.text)


class TestListAccountsEndpoint(unittest.TestCase):
    def test_returns_all_accounts(self):
        admin = AuthenticationAccount.provision(
            account_id="acc-1",
            identity_subject="test-subject",
            email=NormalizedEmail.from_raw("a@e.com"),
            display_name="A",
            user_code="USR-1",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        client, _ = _build_test_app(accounts={"acc-1": admin})
        response = client.get("/api/v1/auth/accounts")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)


if __name__ == "__main__":
    unittest.main()
