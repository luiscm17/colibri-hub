import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from bootstrap.api_router import create_api_router
from bootstrap.http_error_handlers import register_exception_handlers
from warehouse.bales.application import (
    RegisterRawMaterialBatchCommand,
    RegisterRawMaterialBatchResult,
)


class SuccessfulUseCase:
    """Stand-in use case that asserts OpenAPI generation never executes it."""
    
    def execute(
        self, command: RegisterRawMaterialBatchCommand
    ) -> RegisterRawMaterialBatchResult:
        del command
        raise AssertionError("OpenAPI generation must not execute the use case.")


class BaleRegistrationOpenApiTests(unittest.TestCase):
    """OpenAPI schema contract tests for bale registration endpoint."""
    
    def test_documents_only_the_current_post_route_and_contract_responses(self) -> None:
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(create_api_router(lambda: SuccessfulUseCase()))
        client = TestClient(app)

        operation = client.get("/openapi.json").json()["paths"]["/api/v1/warehouse/bales"]

        self.assertEqual(set(operation), {"post"})
        self.assertEqual(set(operation["post"]["responses"]), {"201", "409", "422", "500"})
        self.assertNotIn("/api/v1/warehouse/bales/", client.get("/openapi.json").json()["paths"])
        response_schema = operation["post"]["responses"]["201"]["content"]["application/json"]["schema"]
        self.assertEqual(response_schema["$ref"], "#/components/schemas/BaleReceptionResponse")
