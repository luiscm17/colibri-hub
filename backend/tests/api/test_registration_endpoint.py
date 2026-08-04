import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.tests.support.http_payloads import bale_reception_payload
from backend.tests.support.values import (
    BATCH_ID,
    DTEX,
    RECEIVED_AT,
)
from bootstrap.api_router import create_api_router
from bootstrap.http_error_handlers import register_exception_handlers
from warehouse.bales.adapters.http.router import BaleUseCases
from warehouse.bales.application import (
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
    RegisterRawMaterialBatchCommand,
    RegisterRawMaterialBatchResult,
)
from warehouse.bales.domain.domain_errors import InvalidDtexError
from warehouse.bales.ports.authorization import AuthenticatedIdentity


class RecordingUseCase:
    """Use case double that records commands and returns a pre-set outcome."""
    
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


class _StubUseCase:
    """Stub use case that raises NotImplementedError. Used for unused slots."""

    def execute(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError("Stub use case — should not be called.")


class _AllowAuthorization:
    def require(self, *args: object, **kwargs: object) -> None:
        return None


def registration_result() -> RegisterRawMaterialBatchResult:
    """Build a standard successful registration result for test assertions."""
    return RegisterRawMaterialBatchResult(
        raw_material_batch_id=BATCH_ID,
        shipment_number="SHIP-01",
        received_at=RECEIVED_AT,
        provider_name="Fiber Supplier",
        bale_count=1,
    )


def client_for(
    outcome: RegisterRawMaterialBatchResult | Exception,
) -> tuple[TestClient, RecordingUseCase]:
    """Create a test client and recording use case for endpoint tests."""
    use_case = RecordingUseCase(outcome)
    stub = _StubUseCase()
    use_cases = BaleUseCases(
        register=use_case,  # type: ignore[arg-type]
        stock_summary=stub,  # type: ignore[arg-type]
        bale_detail=stub,  # type: ignore[arg-type]
        deliver=stub,  # type: ignore[arg-type]
    )
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(
        create_api_router(
            lambda: use_cases,
            lambda: AuthenticatedIdentity("test-subject"),
            lambda: _AllowAuthorization(),
            lambda: object(),  # type: ignore[return-value]
            lambda: object(),  # type: ignore[return-value]
        )
    )
    return TestClient(app, raise_server_exceptions=False), use_case


class RegisterBaleEndpointTests(unittest.TestCase):
    """HTTP endpoint contract tests for bale registration route."""
    
    def test_post_registers_collective_payload_and_serializes_current_response(self) -> None:
        client, use_case = client_for(registration_result())

        response = client.post("/api/v1/warehouse/bales", json=bale_reception_payload())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "raw_material_batch_id": str(BATCH_ID),
                "shipment_number": "SHIP-01",
                "received_at": "2026-07-25",
                "provider_name": "Fiber Supplier",
                "bale_count": 1,
            },
        )
        self.assertNotIn("bales", response.json())
        self.assertNotIn("reception_id", response.json())
        self.assertEqual(len(use_case.commands), 1)
        self.assertEqual(use_case.commands[0].received_at, RECEIVED_AT)
        self.assertEqual(use_case.commands[0].bales[0].dtex, DTEX)

    def test_request_validation_rejects_representative_missing_extra_and_invalid_values(self) -> None:
        """Rejects payloads with missing fields, unexpected keys, and invalid timestamps."""
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
        """Only the POST operation exists; trailing slash redirects without executing."""
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
        """Each known error type maps to the documented HTTP status, error code, and field path."""
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
        """Unexpected exceptions produce a generic 500 response and log the original error."""
        client, _ = client_for(RuntimeError("private diagnostic"))

        with self.assertLogs("bootstrap.http_error_handlers", level="ERROR"):
            response = client.post("/api/v1/warehouse/bales", json=bale_reception_payload())

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "internal_server_error")
        self.assertNotIn("private diagnostic", response.text)
