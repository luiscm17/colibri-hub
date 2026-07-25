import asyncio
import unittest
from unittest.mock import MagicMock

from fastapi import FastAPI, Request

from bootstrap.http_error_handlers import (
    register_exception_handlers,
    request_validation_error_handler,
    unexpected_error_handler,
    _validation_error_path,
)
from warehouse.bales.application.errors import (
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
)
from warehouse.bales.domain.domain_errors import DomainError


def _await(coro):
    return asyncio.run(coro)


class TestRegisterExceptionHandlers(unittest.TestCase):
    def test_registers_all_expected_handlers(self) -> None:
        app = FastAPI()
        register_exception_handlers(app)

        registered = {
            exc for exc in app.exception_handlers
            if isinstance(exc, type) and issubclass(exc, Exception)
        }

        self.assertIn(DuplicateShipmentNumberError, registered)
        self.assertIn(DuplicateBaleNumberError, registered)
        self.assertIn(DomainError, registered)

    def test_app_is_fastapi_instance(self) -> None:
        register_exception_handlers(FastAPI())


class TestRequestValidationErrorHandler(unittest.TestCase):
    def test_returns_422_with_field_errors(self) -> None:
        from fastapi.exceptions import RequestValidationError
        from pydantic import ValidationError as PydanticValidationError

        try:
            from pydantic import BaseModel, Field

            class TestModel(BaseModel):
                name: str = Field(min_length=1)

            TestModel.model_validate({"name": ""})
        except PydanticValidationError as pydantic_error:
            validation_error = RequestValidationError(pydantic_error.errors())

        request = MagicMock(spec=Request)
        response = _await(request_validation_error_handler(request, validation_error))

        self.assertEqual(response.status_code, 422)

    def test_error_envelope_has_expected_structure(self) -> None:
        from fastapi.exceptions import RequestValidationError

        mock_errors = [
            {
                "loc": ("body", "shipment_number"),
                "msg": "Field required",
                "type": "missing",
            }
        ]
        validation_error = RequestValidationError(mock_errors)

        request = MagicMock(spec=Request)
        response = _await(request_validation_error_handler(request, validation_error))

        self.assertEqual(response.status_code, 422)
        body = response.body.decode()
        self.assertIn("request_validation_error", body)
        self.assertIn("shipment_number", body)


class TestUnexpectedErrorHandler(unittest.TestCase):
    def test_returns_500_without_details(self) -> None:
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/v1/warehouse/bales"
        error = RuntimeError("Sensitive SQL details")

        response = _await(unexpected_error_handler(request, error))

        self.assertEqual(response.status_code, 500)
        body = response.body.decode()
        self.assertIn("internal_server_error", body)
        self.assertNotIn("Sensitive SQL details", body)


class TestValidationErrorPath(unittest.TestCase):
    def test_strips_body_from_location(self) -> None:
        result = _validation_error_path(("body", "shipment_number"))
        self.assertEqual(result, "shipment_number")

    def test_returns_body_when_only_body(self) -> None:
        result = _validation_error_path(("body",))
        self.assertEqual(result, "body")

    def test_joins_nested_paths(self) -> None:
        result = _validation_error_path(("body", "bales", 0, "bale_number"))
        self.assertEqual(result, "bales.0.bale_number")

    def test_defaults_to_body_for_empty_tuple(self) -> None:
        result = _validation_error_path(())
        self.assertEqual(result, "body")


if __name__ == "__main__":
    unittest.main()
