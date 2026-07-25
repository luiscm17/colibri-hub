import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from warehouse.bales.adapters.http.router import create_router
from warehouse.bales.application.register_raw_material_batch_command import (
    ReceivedBaleCommand,
    RegisterRawMaterialBatchCommand,
)
from warehouse.bales.application.register_raw_material_batch_result import (
    RegisterRawMaterialBatchResult,
    RegisteredBaleResult,
)


class StubRegisterRawMaterialBatch:
    def __init__(self, result: RegisterRawMaterialBatchResult) -> None:
        self.result = result
        self.inputs: list[RegisterRawMaterialBatchCommand] = []

    def execute(
        self, reception_input: RegisterRawMaterialBatchCommand
    ) -> RegisterRawMaterialBatchResult:
        self.inputs.append(reception_input)
        return self.result


def request_payload(bale_count: int) -> dict[str, object]:
    return {
        "shipment_number": "P-260042",
        "received_at": "2026-07-22T10:30:00-04:00",
        "provider_name": "Proveedor Industrial",
        "bales": [
            {
                "bale_number": f"F-{index:03d}",
                "material_type": "HB",
                "dtex": "1.70",
                "gross_weight_kg": "253.40",
                "container_weight_kg": "3.40",
            }
            for index in range(1, bale_count + 1)
        ],
    }


def reception_result(bale_count: int) -> RegisterRawMaterialBatchResult:
    return RegisterRawMaterialBatchResult(
        reception_id=UUID(int=100),
        shipment_number="P-260042",
        received_at=datetime(
            2026, 7, 22, 10, 30, tzinfo=timezone(timedelta(hours=-4))
        ),
        provider_name="Proveedor Industrial",
        bale_count=bale_count,
        bales=tuple(
            RegisteredBaleResult(
                id=UUID(int=index),
                bale_number=f"F-{index:03d}",
                material_type="HB",
                dtex=Decimal("1.70"),
                gross_weight_kg=Decimal("253.40"),
                container_weight_kg=Decimal("3.40"),
                status="in_warehouse",
            )
            for index in range(1, bale_count + 1)
        ),
    )


class TestBaleRouter(unittest.TestCase):
    def test_registers_one_and_multiple_bales_with_201(self) -> None:
        for bale_count in (1, 2):
            with self.subTest(bale_count=bale_count):
                stub = StubRegisterRawMaterialBatch(reception_result(bale_count))
                app = FastAPI()
                app.include_router(
                    create_router(lambda: stub),
                    prefix="/api/v1/warehouse",
                )

                response = TestClient(app).post(
                    "/api/v1/warehouse/bales",
                    json=request_payload(bale_count),
                )

                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.json()["bale_count"], bale_count)
                self.assertEqual(len(stub.inputs), 1)

    def test_maps_request_executes_once_and_maps_result_response(self) -> None:
        stub = StubRegisterRawMaterialBatch(reception_result(2))
        app = FastAPI()
        app.include_router(
            create_router(lambda: stub),
            prefix="/api/v1/warehouse",
        )

        response = TestClient(app).post(
            "/api/v1/warehouse/bales", json=request_payload(2)
        )

        expected_input = RegisterRawMaterialBatchCommand(
            received_at=datetime.fromisoformat("2026-07-22T10:30:00-04:00"),
            shipment_number="P-260042",
            provider_name="Proveedor Industrial",
            bales=tuple(
                ReceivedBaleCommand(
                    bale_number=f"F-{index:03d}",
                    material_type="HB",
                    dtex=Decimal("1.70"),
                    gross_weight_kg=Decimal("253.40"),
                    container_weight_kg=Decimal("3.40"),
                )
                for index in range(1, 3)
            ),
        )
        self.assertEqual(stub.inputs, [expected_input])
        self.assertEqual(
            response.json(),
            {
                "reception_id": str(UUID(int=100)),
                "shipment_number": "P-260042",
                "received_at": "2026-07-22T10:30:00-04:00",
                "provider_name": "Proveedor Industrial",
                "bale_count": 2,
                "bales": [
                    {
                        "id": str(UUID(int=index)),
                        "bale_number": f"F-{index:03d}",
                        "material_type": "HB",
                        "dtex": "1.70",
                        "gross_weight_kg": "253.40",
                        "container_weight_kg": "3.40",
                        "status": "in_warehouse",
                    }
                    for index in range(1, 3)
                ],
            },
        )
        self.assertNotIn("total_net_weight_kg", response.json())
        self.assertTrue(
            all("net_weight_kg" not in bale for bale in response.json()["bales"])
        )


    def test_rejects_empty_bales_with_422(self) -> None:
        stub = StubRegisterRawMaterialBatch(reception_result(1))
        app = FastAPI()
        app.include_router(
            create_router(lambda: stub),
            prefix="/api/v1/warehouse",
        )

        payload = request_payload(1)
        payload["bales"] = []

        response = TestClient(app).post(
            "/api/v1/warehouse/bales", json=payload
        )

        self.assertEqual(response.status_code, 422)

    def test_rejects_missing_body_with_422(self) -> None:
        stub = StubRegisterRawMaterialBatch(reception_result(1))
        app = FastAPI()
        app.include_router(
            create_router(lambda: stub),
            prefix="/api/v1/warehouse",
        )

        response = TestClient(app).post(
            "/api/v1/warehouse/bales", json={}
        )

        self.assertEqual(response.status_code, 422)

    def test_rejects_naive_datetime_with_422(self) -> None:
        stub = StubRegisterRawMaterialBatch(reception_result(1))
        app = FastAPI()
        app.include_router(
            create_router(lambda: stub),
            prefix="/api/v1/warehouse",
        )

        payload = request_payload(1)
        payload["received_at"] = "2026-07-22T10:30:00"

        response = TestClient(app).post(
            "/api/v1/warehouse/bales", json=payload
        )

        self.assertEqual(response.status_code, 422)

    def test_rejects_extra_fields_with_422(self) -> None:
        stub = StubRegisterRawMaterialBatch(reception_result(1))
        app = FastAPI()
        app.include_router(
            create_router(lambda: stub),
            prefix="/api/v1/warehouse",
        )

        payload = request_payload(1)
        payload["unexpected"] = "value"

        response = TestClient(app).post(
            "/api/v1/warehouse/bales", json=payload
        )

        self.assertEqual(response.status_code, 422)

    def test_openapi_spec_lists_error_responses(self) -> None:
        stub = StubRegisterRawMaterialBatch(reception_result(1))
        app = FastAPI()
        app.include_router(
            create_router(lambda: stub),
            prefix="/api/v1/warehouse",
        )

        post = app.openapi()["paths"]["/api/v1/warehouse/bales"]["post"]

        self.assertIn("409", post["responses"])
        self.assertIn("422", post["responses"])
        self.assertIn("500", post["responses"])


if __name__ == "__main__":
    unittest.main()
