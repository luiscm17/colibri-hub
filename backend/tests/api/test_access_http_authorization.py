import unittest
from contextlib import nullcontext

from fastapi import FastAPI
from fastapi.testclient import TestClient

from access.adapters.warehouse_authorization import WarehouseAuthorizationAdapter
from access.application.services import AccessApplication, AccessState
from access.domain.models import (
    SYSTEM_ADMINISTRATOR,
    Action,
    AccessProfile,
    Permission,
    Role,
    RoleAssignment,
    Scope,
    ScopeCode,
)
from backend.tests.support.http_payloads import bale_reception_payload
from backend.tests.support.values import BATCH_ID, RECEIVED_AT
from bootstrap.api_router import create_api_router
from bootstrap.http_application import create_app
from bootstrap.http_error_handlers import register_exception_handlers
from infra.configuration import ApplicationSettings, CorsSettings, DatabaseSettings
from warehouse.bales.adapters.http.router import BaleUseCases
from warehouse.bales.application import RegisterRawMaterialBatchResult
from warehouse.bales.application.get_stock_summary import StockSummaryResult
from warehouse.bales.ports.authorization import AuthenticatedIdentity


class _StateStore:
    def __init__(self, state: AccessState) -> None:
        self.state = state

    def serialized(self):
        return nullcontext()

    def load(self) -> AccessState:
        return self.state

    def commit(self, state: AccessState, audit: object) -> None:
        del audit
        self.state = state


class _RecordingRegister:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, command: object) -> RegisterRawMaterialBatchResult:
        del command
        self.calls += 1
        return RegisterRawMaterialBatchResult(
            raw_material_batch_id=BATCH_ID,
            shipment_number="SHIP-01",
            received_at=RECEIVED_AT,
            provider_name="Fiber Supplier",
            bale_count=1,
        )


class _UnusedUseCase:
    def execute(self, *args: object, **kwargs: object) -> None:
        raise AssertionError("This endpoint should not execute the use case.")


class _StockSummary:
    def execute(self, command: object) -> StockSummaryResult:
        del command
        return StockSummaryResult(0, 0, 0, 0, 0, 0)


def _access_application() -> AccessApplication:
    warehouse_scope = ScopeCode("warehouse.raw_materials")
    return AccessApplication(
        _StateStore(
            AccessState(
                profiles=[
                    AccessProfile("ordinary", "ORDINARY"),
                    AccessProfile("administrator", "ADMIN"),
                    AccessProfile("inactive", "INACTIVE", is_active=False),
                ],
                roles=[
                    Role("warehouse_writer", frozenset({Permission(Action.WRITE, warehouse_scope)})),
                    Role(SYSTEM_ADMINISTRATOR),
                ],
                scopes=[Scope(warehouse_scope)],
                assignments=[
                    RoleAssignment("ordinary", "warehouse_writer"),
                    RoleAssignment("administrator", SYSTEM_ADMINISTRATOR),
                ],
            )
        )
    )


def _client_for(subject: str) -> tuple[TestClient, _RecordingRegister]:
    access_application = _access_application()
    register = _RecordingRegister()
    unused = _UnusedUseCase()
    use_cases = BaleUseCases(
        register=register,  # type: ignore[arg-type]
        stock_summary=_StockSummary(),  # type: ignore[arg-type]
        bale_detail=unused,  # type: ignore[arg-type]
        deliver=unused,  # type: ignore[arg-type]
    )
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(
        create_api_router(
            lambda: use_cases,
            lambda: AuthenticatedIdentity(subject),
            lambda: WarehouseAuthorizationAdapter(access_application),
            lambda: access_application,
        )
    )
    return TestClient(app, raise_server_exceptions=False), register


class AccessHttpAuthorizationTests(unittest.TestCase):
    def test_access_me_returns_ordinary_global_and_specific_self_outcomes(self) -> None:
        ordinary, _ = _client_for("ordinary")
        global_administrator, _ = _client_for("administrator")
        missing, _ = _client_for("missing")
        inactive, _ = _client_for("inactive")

        self.assertEqual(
            ordinary.get("/api/v1/access/me").json(),
            {
                "subject": "ordinary",
                "profile_code": "ORDINARY",
                "global": False,
                "permissions": [{"action": "write", "scope": "warehouse.raw_materials"}],
            },
        )
        self.assertEqual(global_administrator.get("/api/v1/access/me").json()["global"], True)
        self.assertEqual(missing.get("/api/v1/access/me").json(), {"detail": "profile_not_found"})
        self.assertEqual(inactive.get("/api/v1/access/me").json(), {"detail": "profile_inactive"})

    def test_bale_registration_allows_server_derived_permission_and_hides_denial_state(self) -> None:
        allowed, allowed_register = _client_for("ordinary")
        denied, denied_register = _client_for("missing")

        allowed_response = allowed.post("/api/v1/warehouse/bales", json=bale_reception_payload())
        denied_response = denied.post(
            "/api/v1/warehouse/bales",
            json=bale_reception_payload(),
            headers={"X-Roles": "system_administrator", "X-Action": "write"},
        )

        self.assertEqual(allowed_response.status_code, 201)
        self.assertEqual(allowed_register.calls, 1)
        self.assertEqual(denied_response.status_code, 403)
        self.assertEqual(denied_response.json()["error"]["code"], "access_denied")
        self.assertNotIn("profile", denied_response.text)
        self.assertNotIn("role", denied_response.text)
        self.assertEqual(denied_register.calls, 0)

        before_mapping = denied.post(
            "/api/v1/warehouse/bales", json={"roles": ["system_administrator"]}
        )
        self.assertEqual(before_mapping.status_code, 403)
        self.assertEqual(denied_register.calls, 0)

    def test_unaffected_stock_endpoint_does_not_invoke_authorization(self) -> None:
        client, register = _client_for("missing")

        response = client.get("/api/v1/warehouse/bales")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(register.calls, 0)

    def test_production_default_fails_closed_and_cors_allows_authorization_header(self) -> None:
        settings = ApplicationSettings(
            database=DatabaseSettings(url="sqlite+pysqlite:///:memory:"),
            cors=CorsSettings(allowed_origins=["https://example.test"]),
        )
        app = create_app(settings=settings, session_factory=lambda: object())  # type: ignore[arg-type]
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post("/api/v1/warehouse/bales", json=bale_reception_payload())
        preflight = client.options(
            "/api/v1/warehouse/bales",
            headers={
                "Origin": "https://example.test",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("Authorization", preflight.headers["access-control-allow-headers"])
