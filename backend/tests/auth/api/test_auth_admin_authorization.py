"""Tests for C1: auth admin route authorization guard.

Validates that non-admin users receive 403 when accessing auth admin endpoints,
and that admin users can access them normally.
"""

import unittest
from datetime import UTC, datetime

from access.application.authorize_action import AuthorizeAction
from access.domain.actions import Action, Permission
from access.domain.roles import Assignment, Role
from access.domain.scopes import Scope
from access.domain.users import AccessUser
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
from auth.ports.identity_provider import ProviderIdentity
from bootstrap.http_error_handlers import register_exception_handlers
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from shared.identity import AuthenticatedIdentity

NOW = datetime(2026, 8, 6, 12, 0, 0, tzinfo=UTC)

ACCESS_CONTROL_SCOPE = Scope(
    scope_id="scope-ac",
    definition_key="access_control",
    scope_code="access_control",
    scope_name="Access Control",
    owning_context="Access Control",
    description="Access administration",
    is_active=True,
    version=1,
    created_at=NOW,
    updated_at=NOW,
)

ADMIN_USER = AccessUser(
    "user-admin", "admin-subject", "USR-ADM", "Admin", True, 1, 1, NOW, NOW
)
ORDINARY_USER = AccessUser(
    "user-ord", "ordinary-subject", "USR-ORD", "Ordinary", True, 1, 1, NOW, NOW
)

ADMIN_ROLE = Role(
    "role-admin",
    "system_administrator",
    "System Administrator",
    None,
    True,
    True,
    1,
    set(),
)
ORDINARY_ROLE = Role(
    "role-ord",
    "warehouse_reader",
    "Warehouse Reader",
    None,
    False,
    True,
    1,
    {Permission(Action.READ, "warehouse.raw_materials")},
)

ASSIGNMENTS = [
    Assignment("asgn-1", "user-admin", "role-admin", "user-admin", NOW),
    Assignment("asgn-2", "user-ord", "role-ord", "user-admin", NOW),
]


class _FakeUserRepo:
    def find_by_subject(self, identity_subject: str):
        users = [ADMIN_USER, ORDINARY_USER]
        return next((u for u in users if u.identity_subject == identity_subject), None)

    def find_by_id(self, user_id: str):
        users = [ADMIN_USER, ORDINARY_USER]
        return next((u for u in users if u.user_id == user_id), None)

    def list_all(self, **kw):
        return [ADMIN_USER, ORDINARY_USER]

    def count(self):
        return 2

    def save(self, user):
        pass

    def count_active_administrators(self, **kw):
        return 1

    def bump_authorization_version_for_role(self, role_id: str):
        return []

    def bump_authorization_version_for_scope(self, scope_id: str):
        return []


class _FakeRoleRepo:
    def find_by_id(self, role_id: str):
        roles = [ADMIN_ROLE, ORDINARY_ROLE]
        return next((r for r in roles if r.role_id == role_id), None)

    def find_by_code(self, role_code: str):
        roles = [ADMIN_ROLE, ORDINARY_ROLE]
        return next((r for r in roles if r.role_code == role_code), None)

    def find_system_administrator_role(self):
        return ADMIN_ROLE

    def list_all(self, **kw):
        return [ADMIN_ROLE, ORDINARY_ROLE]

    def count(self):
        return 2

    def save(self, role, *, created_by_user_id=None):
        pass


class _FakeAssignmentRepo:
    def find_for_user(self, user_id):
        return [a for a in ASSIGNMENTS if a.user_id == user_id and a.is_current]

    def find_for_role(self, role_id):
        return [a for a in ASSIGNMENTS if a.role_id == role_id and a.is_current]

    def save(self, assignment):
        pass


class _FakeScopeRepo:
    def find_by_id(self, scope_id: str):
        return (
            ACCESS_CONTROL_SCOPE if scope_id == ACCESS_CONTROL_SCOPE.scope_id else None
        )

    def find_by_code(self, scope_code: str):
        return ACCESS_CONTROL_SCOPE if scope_code == "access_control" else None

    def list_all(self, **kw):
        return [ACCESS_CONTROL_SCOPE]

    def count(self):
        return 1

    def save(self, scope):
        pass


class _FakeAccountRepo:
    def __init__(self):
        self.accounts = {}

    def find_by_email(self, email):
        return None

    def find_by_id(self, account_id):
        return self.accounts.get(account_id)

    def find_by_subject(self, identity_subject):
        return next(
            (
                a
                for a in self.accounts.values()
                if a.identity_subject == identity_subject
            ),
            None,
        )

    def list_enabled_administrators(self):
        return []

    def list_all(self):
        return list(self.accounts.values())

    def save(self, account):
        self.accounts[account.account_id] = account


class _FakeAuditRepo:
    def __init__(self):
        self.entries = []

    def append(self, entry):
        self.entries.append(entry)

    def list_by_account(self, account_id):
        return []

    def list_recent(self, limit=50):
        return self.entries[-limit:]

    def list_keyset(self, *, as_of, cursor, limit):
        return []


class _FakeIdentityProvider:
    def create_user(self, *, email, password):
        return ProviderIdentity(subject="prov-sub", email=email)

    def update_password(self, **kw):
        pass

    def ban_user(self, **kw):
        pass

    def unban_user(self, **kw):
        pass

    def revoke_session(self, **kw):
        pass

    def revoke_subject_sessions(self, **kw):
        pass

    def delete_user(self, **kw):
        pass

    def list_successful_login_audit_evidence(self, *, timestamp_to):
        return []

    def has_active_session(self, *, session_id, subject):
        return False


class _FakeAccessProvisioning:
    def provision_profile(self, **kw):
        pass

    def activate_profile(self, **kw):
        pass

    def deactivate_profile(self, **kw):
        pass

    def assert_reduction_allowed(self, subject):
        return None


class _FakeTransaction:
    def commit(self):
        pass


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


def _build_app(subject: str) -> TestClient:
    """Build test app where the specified subject is the authenticated user."""
    user_repo = _FakeUserRepo()
    role_repo = _FakeRoleRepo()
    assignment_repo = _FakeAssignmentRepo()
    scope_repo = _FakeScopeRepo()

    authorize = AuthorizeAction(
        user_repository=user_repo,
        role_repository=role_repo,
        assignment_repository=assignment_repo,
        scope_repository=scope_repo,
    )

    account_repo = _FakeAccountRepo()
    audit_repo = _FakeAuditRepo()
    provider = _FakeIdentityProvider()
    access = _FakeAccessProvisioning()
    clock = _FakeClock()
    identity = _FakeIdentity()
    transaction = _FakeTransaction()

    use_cases = AuthUseCases(
        get_current_authentication=GetCurrentAuthentication(account_repo),
        change_required_password=ChangeRequiredPassword(
            account_repository=account_repo,
            audit_repository=audit_repo,
            clock=clock,
            identity=identity,
        ),
        record_logout=RecordLogout(
            account_repository=account_repo,
            audit_repository=audit_repo,
            identity_provider=provider,
            clock=clock,
            identity=identity,
        ),
        provision_account=ProvisionAccount(
            account_repository=account_repo,
            audit_repository=audit_repo,
            identity_provider=provider,
            access_provisioning=access,
            clock=clock,
            identity=identity,
        ),
        reset_password=ResetPassword(
            account_repository=account_repo,
            audit_repository=audit_repo,
            identity_provider=provider,
            access_provisioning=access,
            transaction=transaction,
            clock=clock,
            identity=identity,
        ),
        disable_account=DisableAccount(
            account_repository=account_repo,
            audit_repository=audit_repo,
            identity_provider=provider,
            access_provisioning=access,
            transaction=transaction,
            clock=clock,
            identity=identity,
        ),
        enable_account=EnableAccount(
            account_repository=account_repo,
            audit_repository=audit_repo,
            identity_provider=provider,
            access_provisioning=access,
            clock=clock,
            identity=identity,
        ),
        get_account=GetAccount(account_repo),
        list_accounts=ListAccounts(account_repo),
        list_audits=ListAudits(audit_repo, account_repo, provider, clock),
    )

    def identity_resolver() -> AuthenticatedIdentity:
        return AuthenticatedIdentity(subject=subject, session_id="ses-test")

    def use_case_factory() -> AuthUseCases:
        return use_cases

    def authorize_action_provider() -> AuthorizeAction:
        return authorize

    app = FastAPI()
    register_exception_handlers(app)
    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(
        create_auth_admin_router(
            identity_resolver, use_case_factory, authorize_action_provider
        )
    )
    app.include_router(api_router)

    return TestClient(app, raise_server_exceptions=False)


class TestAuthAdminAuthorization(unittest.TestCase):
    """C1: auth admin returns 403 for non-admin user."""

    def test_admin_can_list_accounts(self):
        client = _build_app("admin-subject")
        resp = client.get("/api/v1/auth/accounts")
        self.assertEqual(resp.status_code, 200)

    def test_non_admin_gets_403_on_list_accounts(self):
        client = _build_app("ordinary-subject")
        resp = client.get("/api/v1/auth/accounts")
        self.assertEqual(resp.status_code, 403)

    def test_non_admin_gets_403_on_post_accounts(self):
        client = _build_app("ordinary-subject")
        resp = client.post(
            "/api/v1/auth/accounts",
            json={
                "email": "test@example.com",
                "provisional_password": "temp123",
                "user_code": "USR-999",
                "display_name": "Test",
                "role_codes": ["warehouse_reader"],
                "reason": "Test",
            },
        )
        self.assertEqual(resp.status_code, 403)

    def test_non_admin_gets_403_on_audits(self):
        client = _build_app("ordinary-subject")
        resp = client.get("/api/v1/auth/audits")
        self.assertEqual(resp.status_code, 403)

    def test_unmapped_user_gets_403(self):
        client = _build_app("unknown-subject")
        resp = client.get("/api/v1/auth/accounts")
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_list_audits(self):
        client = _build_app("admin-subject")
        resp = client.get("/api/v1/auth/audits")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
