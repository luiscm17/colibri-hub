import json
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from pydantic import ValidationError

from warehouse.bales.adapters.http import (
    BaleReceptionRequest,
    ErrorDetailResponse,
    ErrorResponse,
    FieldErrorResponse,
    bale_reception_to_input,
    bale_reception_to_response,
)
from warehouse.bales.application.register_raw_material_batch_command import (
    ReceivedBaleCommand,
    RegisterRawMaterialBatchCommand,
)
from warehouse.bales.application.register_raw_material_batch_result import (
    RegisterRawMaterialBatchResult,
    RegisteredBaleResult,
)


def valid_bale(bale_number: str = "F-001") -> dict[str, str]:
    return {
        "bale_number": bale_number,
        "material_type": "HB",
        "dtex": "1.70",
        "gross_weight_kg": "253.40",
        "container_weight_kg": "3.40",
    }


def valid_request_data() -> dict[str, object]:
    return {
        "shipment_number": "P-260042",
        "received_at": "2026-07-22T10:30:00-04:00",
        "provider_name": "Proveedor Industrial",
        "bales": [valid_bale()],
    }


class TestBaleReceptionRequest(unittest.TestCase):
    def test_accepts_single_and_multiple_bales(self) -> None:
        single = BaleReceptionRequest.model_validate(valid_request_data())
        multiple_data = valid_request_data()
        multiple_data["bales"] = [valid_bale("F-001"), valid_bale("F-002")]
        multiple = BaleReceptionRequest.model_validate(multiple_data)

        self.assertEqual(len(single.bales), 1)
        self.assertEqual([item.bale_number for item in multiple.bales], ["F-001", "F-002"])

    def test_rejects_empty_bales(self) -> None:
        data = valid_request_data()
        data["bales"] = []

        with self.assertRaises(ValidationError):
            BaleReceptionRequest.model_validate(data)

    def test_requires_aware_datetime(self) -> None:
        data = valid_request_data()
        data["received_at"] = "2026-07-22T10:30:00"

        with self.assertRaises(ValidationError) as context:
            BaleReceptionRequest.model_validate(data)

        self.assertEqual(context.exception.errors()[0]["type"], "timezone_aware")

    def test_preserves_aware_datetime_offset(self) -> None:
        request = BaleReceptionRequest.model_validate(valid_request_data())

        self.assertEqual(request.received_at.utcoffset(), timedelta(hours=-4))

    def test_decimal_strings_become_decimal_and_retain_scale(self) -> None:
        request = BaleReceptionRequest.model_validate(valid_request_data())
        bale = request.bales[0]

        self.assertEqual(bale.dtex, Decimal("1.70"))
        self.assertEqual(bale.dtex.as_tuple().exponent, -2)
        self.assertEqual(bale.gross_weight_kg, Decimal("253.40"))
        self.assertEqual(bale.container_weight_kg, Decimal("3.40"))

    def test_rejects_non_string_decimal_inputs_from_json(self) -> None:
        for value in (1.7, 1, True, None, ["1.70"], {"value": "1.70"}):
            with self.subTest(value=value):
                data = valid_request_data()
                data["bales"][0]["dtex"] = value  # type: ignore[index]

                with self.assertRaises(ValidationError):
                    BaleReceptionRequest.model_validate_json(json.dumps(data))

    def test_rejects_non_finite_decimal_strings(self) -> None:
        for value in ("NaN", "Infinity", "-Infinity", "sNaN"):
            with self.subTest(value=value):
                data = valid_request_data()
                data["bales"][0]["gross_weight_kg"] = value  # type: ignore[index]

                with self.assertRaises(ValidationError):
                    BaleReceptionRequest.model_validate(data)

    def test_rejects_extra_fields_at_both_levels(self) -> None:
        top_level = valid_request_data()
        top_level["unexpected"] = "value"
        nested = valid_request_data()
        nested["bales"][0]["unexpected"] = "value"  # type: ignore[index]

        with self.assertRaises(ValidationError):
            BaleReceptionRequest.model_validate(top_level)
        with self.assertRaises(ValidationError):
            BaleReceptionRequest.model_validate(nested)

    def test_models_are_frozen(self) -> None:
        request = BaleReceptionRequest.model_validate(valid_request_data())

        with self.assertRaises(ValidationError):
            request.shipment_number = "P-OTHER"  # type: ignore[misc]
        with self.assertRaises(ValidationError):
            request.bales[0].dtex = Decimal("2.00")  # type: ignore[misc]


class TestBaleReceptionMapping(unittest.TestCase):
    def test_maps_request_to_application_input_exactly(self) -> None:
        data = valid_request_data()
        data["bales"] = [valid_bale("F-001"), valid_bale("F-002")]
        request = BaleReceptionRequest.model_validate(data)

        mapped = bale_reception_to_input(request)

        self.assertIsInstance(mapped, RegisterRawMaterialBatchCommand)
        self.assertEqual(mapped.received_at, request.received_at)
        self.assertEqual(mapped.shipment_number, "P-260042")
        self.assertEqual(mapped.provider_name, "Proveedor Industrial")
        self.assertEqual([item.bale_number for item in mapped.bales], ["F-001", "F-002"])
        self.assertTrue(all(isinstance(item, ReceivedBaleCommand) for item in mapped.bales))
        self.assertTrue(all(isinstance(item.dtex, Decimal) for item in mapped.bales))

    def test_maps_result_to_response_exactly(self) -> None:
        received_at = datetime(2026, 7, 22, 10, 30, tzinfo=timezone(timedelta(hours=-4)))
        raw_material_batch_id = UUID("7a367a1e-18eb-4568-9548-563cd889f121")
        bale_ids = (
            UUID("f247354b-009a-42fa-94f7-9b55442fbe71"),
            UUID("24d72ee3-61dd-456b-a47d-c82d119dfcbc"),
        )
        result = RegisterRawMaterialBatchResult(
            raw_material_batch_id=raw_material_batch_id,
            shipment_number="P-260042",
            received_at=received_at,
            provider_name="Proveedor Industrial",
            bale_count=2,
            bales=tuple(
                RegisteredBaleResult(
                    id=bale_id,
                    bale_number=f"F-00{index}",
                    material_type="HB",
                    dtex=Decimal("1.70"),
                    gross_weight_kg=Decimal("253.40"),
                    container_weight_kg=Decimal("3.40"),
                    status="in_warehouse",
                )
                for index, bale_id in enumerate(bale_ids, start=1)
            ),
        )

        response = bale_reception_to_response(result)

        self.assertEqual(response.raw_material_batch_id, raw_material_batch_id)
        self.assertEqual(response.received_at, received_at)
        self.assertEqual(response.received_at.utcoffset(), timedelta(hours=-4))
        self.assertEqual([item.id for item in response.bales], list(bale_ids))
        self.assertEqual([item.bale_number for item in response.bales], ["F-001", "F-002"])
        self.assertTrue(all(item.status == "in_warehouse" for item in response.bales))
        self.assertTrue(all(isinstance(item.dtex, Decimal) for item in response.bales))

        payload = json.loads(response.model_dump_json())
        self.assertEqual(payload["raw_material_batch_id"], str(raw_material_batch_id))
        self.assertNotIn("reception_id", payload)
        self.assertEqual(payload["bales"][0]["dtex"], "1.70")
        self.assertEqual(payload["bales"][0]["gross_weight_kg"], "253.40")
        self.assertEqual(payload["bales"][0]["container_weight_kg"], "3.40")
        self.assertNotIn("net_weight_kg", payload["bales"][0])
        self.assertNotIn("total_net_weight_kg", payload)

    def test_rejects_unexpected_application_result_status(self) -> None:
        result = RegisterRawMaterialBatchResult(
            raw_material_batch_id=UUID("7a367a1e-18eb-4568-9548-563cd889f121"),
            shipment_number="P-260042",
            received_at=datetime(2026, 7, 22, 10, 30, tzinfo=timezone.utc),
            provider_name="Proveedor Industrial",
            bale_count=1,
            bales=(
                RegisteredBaleResult(
                    id=UUID("f247354b-009a-42fa-94f7-9b55442fbe71"),
                    bale_number="F-001",
                    material_type="HB",
                    dtex=Decimal("1.70"),
                    gross_weight_kg=Decimal("253.40"),
                    container_weight_kg=Decimal("3.40"),
                    status="delivered",
                ),
            ),
        )

        with self.assertRaisesRegex(
            ValueError,
            "Unexpected registered bale status: 'delivered'",
        ):
            bale_reception_to_response(result)


class TestErrorResponse(unittest.TestCase):
    def test_serializes_stable_error_envelope(self) -> None:
        response = ErrorResponse(
            error=ErrorDetailResponse(
                code="shipment_number_already_exists",
                message="A raw material reception already uses this shipment number.",
                fields=(
                    FieldErrorResponse(
                        path="shipment_number",
                        message="Shipment number P-260042 is already registered.",
                    ),
                ),
            )
        )

        self.assertEqual(
            response.model_dump(mode="json"),
            {
                "error": {
                    "code": "shipment_number_already_exists",
                    "message": "A raw material reception already uses this shipment number.",
                    "fields": [
                        {
                            "path": "shipment_number",
                            "message": "Shipment number P-260042 is already registered.",
                        }
                    ],
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
