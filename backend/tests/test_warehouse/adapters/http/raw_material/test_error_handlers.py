import asyncio
import json
import unittest
from unittest.mock import MagicMock

from fastapi import Request

from warehouse.bales.adapters.http.error_handlers import (
    domain_error_handler,
    duplicate_bale_number_handler,
    duplicate_shipment_number_handler,
)
from warehouse.bales.application.errors import (
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
)
from warehouse.bales.domain.domain_errors import DomainError


def _await(coro):
    return asyncio.run(coro)


def _make_mock_request() -> MagicMock:
    return MagicMock(spec=Request)


class TestDuplicateShipmentNumberHandler(unittest.TestCase):
    def test_returns_409_conflict(self) -> None:
        request = _make_mock_request()
        error = DuplicateShipmentNumberError(
            "A raw material reception already uses this shipment number."
        )

        response = _await(duplicate_shipment_number_handler(request, error))

        self.assertEqual(response.status_code, 409)

    def test_returns_expected_error_body(self) -> None:
        request = _make_mock_request()
        error = DuplicateShipmentNumberError(
            "A raw material reception already uses this shipment number."
        )

        response = _await(duplicate_shipment_number_handler(request, error))
        body = json.loads(response.body.decode())

        self.assertEqual(body["error"]["code"], "duplicate_shipment_number")
        self.assertEqual(
            body["error"]["fields"][0]["path"], "shipment_number"
        )
        self.assertEqual(
            body["error"]["fields"][0]["message"],
            "The shipment number must be unique.",
        )


class TestDuplicateBaleNumberHandler(unittest.TestCase):
    def test_returns_422_unprocessable_entity(self) -> None:
        request = _make_mock_request()
        error = DuplicateBaleNumberError(
            "Raw material reception cannot contain duplicate bale numbers."
        )

        response = _await(duplicate_bale_number_handler(request, error))

        self.assertEqual(response.status_code, 422)

    def test_returns_expected_error_body(self) -> None:
        request = _make_mock_request()
        error = DuplicateBaleNumberError(
            "Raw material reception cannot contain duplicate bale numbers."
        )

        response = _await(duplicate_bale_number_handler(request, error))
        body = json.loads(response.body.decode())

        self.assertEqual(body["error"]["code"], "duplicate_bale_number")
        self.assertEqual(
            body["error"]["fields"][0]["path"],
            "bales[].bale_number",
        )
        self.assertEqual(
            body["error"]["fields"][0]["message"],
            "Bale numbers must be unique.",
        )


class TestDomainErrorHandler(unittest.TestCase):
    def test_returns_422_unprocessable_entity(self) -> None:
        request = _make_mock_request()
        error = DomainError("Invalid domain state.")

        response = _await(domain_error_handler(request, error))

        self.assertEqual(response.status_code, 422)

    def test_includes_domain_error_message(self) -> None:
        request = _make_mock_request()
        error = DomainError("Bale weight cannot be negative.")

        response = _await(domain_error_handler(request, error))
        body = json.loads(response.body.decode())

        self.assertEqual(body["error"]["code"], "domain_validation_error")
        self.assertEqual(
            body["error"]["message"],
            "Bale weight cannot be negative.",
        )


if __name__ == "__main__":
    unittest.main()
