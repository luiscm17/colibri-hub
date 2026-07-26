import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.tests.support.http_payloads import bale_reception_payload
from backend.tests.support.values import (
    BALE_ID_1,
    BATCH_ID,
    CONTAINER_WEIGHT_KG,
    DTEX,
    GROSS_WEIGHT_KG,
    RECEIVED_AT,
)
from bootstrap.api_router import create_api_router
from bootstrap.http_error_handlers import register_exception_handlers
from warehouse.bales.application import (
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
    RegisterRawMaterialBatchCommand,
    RegisterRawMaterialBatchResult,
    RegisteredBaleResult,
)
from warehouse.bales.domain.domain_errors import InvalidDtexError


class RecordingUseCase:
    def __init__(self, outcome: RegisterRawMaterialBatchResult | Exception) -> None:
        self.outcome = outcome
        self.commands: list[RegisterRawMaterialBatchCommand] = []

    def execute(
        self, command: RegisterRawMaterialBatchCommand
    ) -> RegisterRawMaterialBatchResult:
        self.commands.append(command)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def registration_result() -> RegisterRawMaterialBatchResult:
    return RegisterRawMaterialBatchResult(
        raw_material_batch_id=BATCH_ID,
        shipment_number="SHIP-01",
        received_at=RECEIVED_AT,
        provider_name="Fiber Supplier",
        bale_count=1,
        bales=(
            RegisteredBaleResult(
                id=BALE_ID_1,
                bale_number="BALE-01",
                material_type="COTTON",
                dtex=DTEX,
                gross_weight_kg=GROSS_WEIGHT_KG,
                container_weight_kg=CONTAINER_WEIGHT_KG,
                status="in_warehouse",
            ),
        ),
    )


def client_for(
    outcome: RegisterRawMaterialBatchResult | Exception,
) -> tuple[TestClient, RecordingUseCase]:
    use_case = RecordingUseCase(outcome)
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(create_api_router(lambda: use_case))
    return TestClient(app, raise_server_exceptions=False), use_case


class RegisterBaleEndpointTests(unittest.TestCase):
    def test_post_registers_collective_payload_and_serializes_current_response(self) -> None:
        client, use_case = client_for(registration_result())

        response = client.post("/api/v1/warehouse/bales", json=bale_reception_payload())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "raw_material_batch_id": str(BATCH_ID),
                "shipment_number": "SHIP-01",
                "received_at": "2026-07-25T10:30:00Z",
                "provider_name": "Fiber Supplier",
                "bale_count": 1,
                "bales": [
                    {
                        "id": str(BALE_ID_1),
                        "bale_number": "BALE-01",
                        "material_type": "COTTON",
                        "dtex": "200.5",
                        "gross_weight_kg": "25.5",
                        "container_weight_kg": "0.5",
                        "status": "in_warehouse",
                    }
                ],
            },
        )
        self.assertNotIn("reception_id", response.json())
        self.assertEqual(len(use_case.commands), 1)
        self.assertEqual(use_case.commands[0].received_at, RECEIVED_AT)
        self.assertEqual(use_case.commands[0].bales[0].dtex, DTEX)

    def test_request_validation_rejects_representative_missing_extra_and_invalid_values(self) -> None:
        client, use_case = client_for(registration_result())
        invalid_payloads = (
            {key: value for key, value in bale_reception_payload().items() if key != "shipment_number"},
            {**bale_reception_payload(), "unexpected": True},
            {**bale_reception_payload(), "received_at": "2026-07-25T10:30:00"},
        )

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = client.post("/api/v1/warehouse/bales", json=payload)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["error"]["code"], "request_validation_error")
        self.assertEqual(use_case.commands, [])

    def test_route_has_one_post_operation_and_trailing_slash_redirects_without_execution(self) -> None:
        client, use_case = client_for(registration_result())

        response = client.post(
            "/api/v1/warehouse/bales/",
            json=bale_reception_payload(),
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 307)
        self.assertTrue(response.headers["location"].endswith("/api/v1/warehouse/bales"))
        self.assertEqual(use_case.commands, [])

    def test_maps_domain_and_application_errors_to_documented_envelopes(self) -> None:
        cases = (
            (
                DuplicateShipmentNumberError("Shipment number is already registered."),
                409,
                "duplicate_shipment_number",
                "shipment_number",
            ),
            (
                DuplicateBaleNumberError("Raw material reception cannot contain duplicate bale numbers."),
                422,
                "duplicate_bale_number",
                "bales[].bale_number",
            ),
            (InvalidDtexError("Dtex must be greater than zero."), 422, "domain_validation_error", None),
        )

        for error, status_code, code, field in cases:
            with self.subTest(error=type(error).__name__):
                client, _ = client_for(error)
                response = client.post("/api/v1/warehouse/bales", json=bale_reception_payload())
                body = response.json()["error"]
                self.assertEqual(response.status_code, status_code)
                self.assertEqual(body["code"], code)
                if field is not None:
                    self.assertEqual(body["fields"][0]["path"], field)

    def test_maps_unexpected_errors_without_exposing_exception_detail(self) -> None:
        client, _ = client_for(RuntimeError("private diagnostic"))

        with self.assertLogs("bootstrap.http_error_handlers", level="ERROR"):
            response = client.post("/api/v1/warehouse/bales", json=bale_reception_payload())

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "internal_server_error")
        self.assertNotIn("private diagnostic", response.text)
