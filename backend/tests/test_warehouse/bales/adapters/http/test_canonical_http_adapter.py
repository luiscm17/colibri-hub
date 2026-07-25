import unittest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from bootstrap.http_error_handlers import register_exception_handlers
from warehouse.bales.application.errors import (
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
)
from warehouse.bales.application.register_raw_material_batch_result import (
    RegisterRawMaterialBatchResult,
    RegisteredBaleResult,
)


def request_payload() -> dict[str, object]:
    return {
        "shipment_number": "SHIP-001",
        "received_at": "2026-07-22T10:30:00+00:00",
        "provider_name": "Provider",
        "bales": [{
            "bale_number": "BAL-001",
            "material_type": "HB",
            "dtex": "1.70",
            "gross_weight_kg": "253.40",
            "container_weight_kg": "3.40",
        }],
    }


class StubUseCase:
    def __init__(self, outcome: object) -> None:
        self.outcome = outcome

    def execute(self, command: object) -> object:
        del command
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def successful_result() -> RegisterRawMaterialBatchResult:
    return RegisterRawMaterialBatchResult(
        reception_id=UUID(int=1),
        shipment_number="SHIP-001",
        received_at=datetime(2026, 7, 22, 10, 30, tzinfo=timezone.utc),
        provider_name="Provider",
        bale_count=1,
        bales=(RegisteredBaleResult(
            id=UUID(int=2), bale_number="BAL-001", material_type="HB",
            dtex=Decimal("1.70"), gross_weight_kg=Decimal("253.40"),
            container_weight_kg=Decimal("3.40"), status="in_warehouse",
        ),),
    )


class TestCanonicalHttpAdapter(unittest.TestCase):
    def test_canonical_router_is_available(self) -> None:
        from warehouse.bales.adapters.http.router import create_router

        self.assertTrue(callable(create_router))

    def test_runtime_contract_has_one_route_openapi_slash_and_error_envelopes(self) -> None:
        from warehouse.bales.adapters.http.router import create_router

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(create_router(lambda: StubUseCase(successful_result())), prefix="/api/v1/warehouse")
        client = TestClient(app, raise_server_exceptions=False)

        post_paths = [
            path
            for path, operations in app.openapi()["paths"].items()
            if list(operations) == ["post"]
        ]
        self.assertEqual(post_paths, ["/api/v1/warehouse/bales"])
        response = client.post("/api/v1/warehouse/bales", json=request_payload())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["reception_id"], str(UUID(int=1)))
        slash = client.post("/api/v1/warehouse/bales/", json=request_payload(), follow_redirects=False)
        self.assertEqual(slash.status_code, 307)

        for error, status_code, code in (
            (DuplicateShipmentNumberError("already registered"), 409, "duplicate_shipment_number"),
            (DuplicateBaleNumberError("duplicate"), 422, "duplicate_bale_number"),
            (RuntimeError("Sensitive SQL details"), 500, "internal_server_error"),
        ):
            app = FastAPI()
            register_exception_handlers(app)
            app.include_router(create_router(lambda error=error: StubUseCase(error)), prefix="/api/v1/warehouse")
            response = TestClient(app, raise_server_exceptions=False).post("/api/v1/warehouse/bales", json=request_payload())
            self.assertEqual(response.status_code, status_code)
            self.assertEqual(response.json()["error"]["code"], code)
            self.assertNotIn("Sensitive SQL details", response.text)


if __name__ == "__main__":
    unittest.main()
