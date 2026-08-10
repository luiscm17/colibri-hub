"""API tests for access HTTP authorization behavior.

Tests that:
- /access/me returns ordinary and global authorization shapes
- Bale registration is denied for unmapped/inactive users
- Bale registration is allowed for authorized users
- Unaffected endpoints do not invoke authorization
- Production default fails closed with 401
- CORS allows Authorization header
"""

import unittest
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from access.adapters.warehouse_authorization import WarehouseAuthorizationAdapter
from access.application.authorize_action import AuthorizeAction
from access.application.get_current_access import GetCurrentAccess
from access.domain.actions import Action, Permission
from access.domain.roles import Assignment, Role
from access.domain.scopes import Scope
from access.domain.users import AccessUser
from bootstrap.api_router import create_api_router
from bootstrap.http_application import create_app
from bootstrap.http_error_handlers import register_exception_handlers
from fastapi import FastAPI
from fastapi.testclient import TestClient
from infra.configuration import ApplicationSettings, CorsSettings, DatabaseSettings
from pydantic import SecretStr
from sqlalchemy.orm import Session
from warehouse.bales.adapters.http.router import BaleUseCases
from warehouse.bales.application import RegisterRawMaterialBatchResult
from warehouse.bales.application.deliver_bales import DeliverBales
from warehouse.bales.application.get_bale_detail import GetBaleDetail
from warehouse.bales.application.get_stock_summary import (
    GetStockSummary,
    StockSummaryResult,
)
from warehouse.bales.application.register_raw_material_batch import (
    RegisterRawMaterialBatch,
)
from warehouse.bales.ports.authorization import AuthenticatedIdentity

from backend.tests.support.http_payloads import bale_reception_payload
from backend.tests.support.values import BATCH_ID, RECEIVED_AT

NOW = datetime(2025, 1, 1, tzinfo=UTC)

# --- In-memory test doubles implementing repository protocols ---

_WAREHOUSE_SCOPE = Scope(
    scope_id="scope-1",
    definition_key="warehouse.raw_materials",
    scope_code="warehouse.raw_materials",
    scope_name="Warehouse Raw Materials",
    owning_context="Warehouse",
    description="Raw materials",
    is_active=True,
    version=1,
    created_at=NOW,
    updated_at=NOW,
)

_USERS = [
    AccessUser("user-1", "ordinary", "USR-ORD", "Ordinary User", True, 1, 1, NOW, NOW),
    AccessUser("user-2", "administrator", "USR-ADM", "Admin User", True, 1, 1, NOW, NOW),
    AccessUser("user-3", "inactive", "USR-INA", "Inactive User", False, 1, 1, NOW, NOW),
]

_ROLES = [
    Role("role-1", "warehouse_writer", "Warehouse Writer", None, False, True, 1,
         {Permission(Action.WRITE, "warehouse.raw_materials")}),
    Role("role-2", "system_administrator", "System Administrator", None, True, True, 1, set()),
]

_ASSIGNMENTS = [
    Assignment("asgn-1", "user-1", "role-1", "user-2", NOW),
    Assignment("asgn-2", "user-2", "role-2", "user-2", NOW),
]


class _FakeUserRepo:
    def find_by_subject(self, identity_subject: str) -> AccessUser | None:
        return next((u for u in _USERS if u.identity_subject == identity_subject), None)

    def find_by_id(self, user_id: str) -> AccessUser | None:
        return next((u for u in _USERS if u.user_id == user_id), None)

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[AccessUser]:
        result = _USERS
        if offset:
            result = result[offset:]
        if limit is not None:
            result = result[:limit]
        return result

    def count(self) -> int:
        return len(_USERS)

    def save(self, user: AccessUser) -> None:
        pass

    def count_active_administrators(
        self,
        *,
        exclude_user_id: str | None = None,
        for_update: bool = False,
    ) -> int:
        return 1

    def bump_authorization_version_for_role(self, role_id: str) -> list[str]:
        return []

    def bump_authorization_version_for_scope(self, scope_id: str) -> list[str]:
        return []


class _FakeRoleRepo:
    def find_by_id(self, role_id: str) -> Role | None:
        return next((r for r in _ROLES if r.role_id == role_id), None)

    def find_by_code(self, role_code: str) -> Role | None:
        return next((r for r in _ROLES if r.role_code == role_code), None)

    def find_system_administrator_role(self) -> Role | None:
        return next((r for r in _ROLES if r.is_system_administrator), None)

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[Role]:
        result = _ROLES
        if offset:
            result = result[offset:]
        if limit is not None:
            result = result[:limit]
        return result

    def count(self) -> int:
        return len(_ROLES)

    def save(self, role: Role, *, created_by_user_id: str | None = None) -> None:
        pass


class _FakeAssignmentRepo:
    def find_for_user(self, user_id: str) -> list[Assignment]:
        return [a for a in _ASSIGNMENTS if a.user_id == user_id and a.is_current]

    def find_for_role(self, role_id: str) -> list[Assignment]:
        return [a for a in _ASSIGNMENTS if a.role_id == role_id and a.is_current]

    def save(self, assignment: Assignment) -> None:
        pass


class _FakeScopeRepo:
    def find_by_id(self, scope_id: str) -> Scope | None:
        return _WAREHOUSE_SCOPE if scope_id == "scope-1" else None

    def find_by_code(self, scope_code: str) -> Scope | None:
        return _WAREHOUSE_SCOPE if scope_code == "warehouse.raw_materials" else None

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[Scope]:
        result = [_WAREHOUSE_SCOPE]
        if offset:
            result = result[offset:]
        if limit is not None:
            result = result[:limit]
        return result

    def count(self) -> int:
        return 1

    def save(self, scope: Scope) -> None:
        pass


class _RecordingRegister:
    def __init__(self):
        self.calls = 0

    def execute(self, command):
        self.calls += 1
        return RegisterRawMaterialBatchResult(
            raw_material_batch_id=BATCH_ID,
            shipment_number="SHIP-01",
            received_at=RECEIVED_AT,
            provider_name="Fiber Supplier",
            bale_count=1,
        )


class _StockSummary:
    def execute(self, command):
        return StockSummaryResult(0, 0, 0, Decimal(0), Decimal(0), Decimal(0))


class _UnusedUseCase:
    def execute(self, *a, **kw):
        raise AssertionError("Should not execute.")


def _client_for(subject: str) -> tuple[TestClient, _RecordingRegister]:
    user_repo = _FakeUserRepo()
    role_repo = _FakeRoleRepo()
    assignment_repo = _FakeAssignmentRepo()
    scope_repo = _FakeScopeRepo()

    authorize = AuthorizeAction(
        user_repository=user_repo, role_repository=role_repo,
        assignment_repository=assignment_repo, scope_repository=scope_repo
    )
    get_current = GetCurrentAccess(
        user_repository=user_repo, role_repository=role_repo,
        assignment_repository=assignment_repo, scope_repository=scope_repo
    )

    register = _RecordingRegister()
    use_cases = BaleUseCases(
        register=cast(RegisterRawMaterialBatch, register),
        stock_summary=cast(GetStockSummary, _StockSummary()),
        bale_detail=cast(GetBaleDetail, _UnusedUseCase()),
        deliver=cast(DeliverBales, _UnusedUseCase()),
    )
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(
        create_api_router(
            lambda: use_cases,
            lambda: AuthenticatedIdentity(subject),
            lambda: WarehouseAuthorizationAdapter(authorize),
            lambda: get_current,
            lambda: authorize,
        )
    )
    return TestClient(app, raise_server_exceptions=False), register


class AccessHttpAuthorizationTests(unittest.TestCase):
    def test_access_me_ordinary_and_global(self):
        ordinary, _ = _client_for("ordinary")
        admin, _ = _client_for("administrator")
        missing, _ = _client_for("missing")
        inactive, _ = _client_for("inactive")

        resp = ordinary.get("/api/v1/access/me")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["authorization"]["is_global"])
        self.assertEqual(
            data["authorization"]["permissions"],
            [{"action": "write", "scope_code": "warehouse.raw_materials"}],
        )
        self.assertIn("roles", data)
        self.assertEqual(
            data["roles"],
            [{"role_id": "role-1", "code": "warehouse_writer", "name": "Warehouse Writer"}],
        )

        resp = admin.get("/api/v1/access/me")
        admin_data = resp.json()
        self.assertTrue(admin_data["authorization"]["is_global"])
        self.assertEqual(
            admin_data["roles"],
            [{"role_id": "role-2", "code": "system_administrator", "name": "System Administrator"}],
        )

        self.assertEqual(missing.get("/api/v1/access/me").json(), {"detail": "profile_not_found"})
        self.assertEqual(inactive.get("/api/v1/access/me").json(), {"detail": "profile_inactive"})

    def test_bale_registration_authorization(self):
        allowed, allowed_reg = _client_for("ordinary")
        denied, denied_reg = _client_for("missing")

        resp = allowed.post("/api/v1/warehouse/bales", json=bale_reception_payload())
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(allowed_reg.calls, 1)

        resp = denied.post("/api/v1/warehouse/bales", json=bale_reception_payload())
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(denied_reg.calls, 0)

    def test_unaffected_stock_endpoint(self):
        client, reg = _client_for("missing")
        resp = client.get("/api/v1/warehouse/bales")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(reg.calls, 0)

    def test_production_default_fails_closed_and_cors(self):
        settings = ApplicationSettings(
            database=DatabaseSettings(url=SecretStr("sqlite+pysqlite:///:memory:")),
            cors=CorsSettings(allowed_origins=["https://example.test"]),
        )
        app = create_app(
            settings=settings,
            session_factory=lambda: cast(Session, object()),
        )
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.post("/api/v1/warehouse/bales", json=bale_reception_payload())
        self.assertEqual(resp.status_code, 401)

        preflight = client.options(
            "/api/v1/warehouse/bales",
            headers={
                "Origin": "https://example.test",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        self.assertIn("Authorization", preflight.headers["access-control-allow-headers"])


if __name__ == "__main__":
    unittest.main()
