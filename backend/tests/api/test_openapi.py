import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from bootstrap.api_router import create_api_router
from bootstrap.http_error_handlers import register_exception_handlers
from warehouse.bales.adapters.http.router import BaleUseCases
from warehouse.bales.application import (
    RegisterRawMaterialBatchCommand,
    RegisterRawMaterialBatchResult,
)


class _StubUseCase:
    """Stand-in use case that asserts OpenAPI generation never executes it."""

    def execute(self, *args: object, **kwargs: object) -> None:
        raise AssertionError("OpenAPI generation must not execute any use case.")


def _build_stub_use_cases() -> BaleUseCases:
    """Build a BaleUseCases container with stub use cases for OpenAPI tests."""
    stub = _StubUseCase()
    return BaleUseCases(
        register=stub,  # type: ignore[arg-type]
        stock_summary=stub,  # type: ignore[arg-type]
        bale_detail=stub,  # type: ignore[arg-type]
        deliver=stub,  # type: ignore[arg-type]
    )


class BaleRegistrationOpenApiTests(unittest.TestCase):
    """OpenAPI schema contract tests for bale management endpoints."""

    def test_documents_all_bale_endpoints_with_expected_operations(self) -> None:
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(create_api_router(lambda: _build_stub_use_cases()))
        client = TestClient(app)

        schema = client.get("/openapi.json").json()
        paths = schema["paths"]

        # /api/v1/warehouse/bales has both GET (stock summary) and POST (registration)
        bales_path = paths["/api/v1/warehouse/bales"]
        self.assertEqual(set(bales_path), {"get", "post"})
        self.assertEqual(set(bales_path["post"]["responses"]), {"201", "409", "422", "500"})
        self.assertEqual(set(bales_path["get"]["responses"]), {"200", "422", "500"})

        # POST response uses the BaleReceptionResponse schema
        post_response_schema = bales_path["post"]["responses"]["201"]["content"]["application/json"]["schema"]
        self.assertEqual(post_response_schema["$ref"], "#/components/schemas/BaleReceptionResponse")

        # GET response uses the StockSummaryResponse schema
        get_response_schema = bales_path["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertEqual(get_response_schema["$ref"], "#/components/schemas/StockSummaryResponse")

        # Bale detail endpoint exists
        detail_path = "/api/v1/warehouse/bales/{shipment_number}/{bale_number}"
        self.assertIn(detail_path, paths)
        self.assertIn("get", paths[detail_path])
        self.assertEqual(set(paths[detail_path]["get"]["responses"]), {"200", "404", "422", "500"})

        # Deliver endpoint exists
        deliver_path = "/api/v1/warehouse/bales/deliver"
        self.assertIn(deliver_path, paths)
        self.assertIn("post", paths[deliver_path])
        self.assertEqual(set(paths[deliver_path]["post"]["responses"]), {"200", "207", "422", "500"})
