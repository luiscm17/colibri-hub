import json
import unittest

from warehouse.adapters.http.raw_material.error_mapping import (
    error_json_response,
)
from warehouse.adapters.http.raw_material.error_response import (
    FieldErrorResponse,
)


class TestErrorJsonResponse(unittest.TestCase):
    def test_returns_expected_status_code(self) -> None:
        response = error_json_response(
            status_code=409,
            code="duplicate_shipment_number",
            message="Shipment number is already registered.",
        )

        self.assertEqual(response.status_code, 409)

    def test_returns_stable_envelope_without_fields(self) -> None:
        response = error_json_response(
            status_code=422,
            code="validation_error",
            message="The request is invalid.",
        )

        body = json.loads(response.body.decode())
        self.assertEqual(
            body,
            {
                "error": {
                    "code": "validation_error",
                    "message": "The request is invalid.",
                    "fields": [],
                }
            },
        )

    def test_includes_field_errors_when_provided(self) -> None:
        response = error_json_response(
            status_code=422,
            code="validation_error",
            message="The request is invalid.",
            fields=(
                FieldErrorResponse(
                    path="shipment_number",
                    message="Shipment number is required.",
                ),
                FieldErrorResponse(
                    path="bales",
                    message="At least one bale is required.",
                ),
            ),
        )

        body = json.loads(response.body.decode())
        self.assertEqual(
            body,
            {
                "error": {
                    "code": "validation_error",
                    "message": "The request is invalid.",
                    "fields": [
                        {
                            "path": "shipment_number",
                            "message": "Shipment number is required.",
                        },
                        {
                            "path": "bales",
                            "message": "At least one bale is required.",
                        },
                    ],
                }
            },
        )

    def test_uses_json_content_type(self) -> None:
        response = error_json_response(
            status_code=400,
            code="bad_request",
            message="Bad request.",
        )

        self.assertEqual(
            response.headers["content-type"],
            "application/json",
        )

    def test_field_errors_defaults_to_empty_tuple(self) -> None:
        response = error_json_response(
            status_code=500,
            code="internal_error",
            message="Internal error.",
        )

        body = json.loads(response.body.decode())
        self.assertEqual(body["error"]["fields"], [])


if __name__ == "__main__":
    unittest.main()
