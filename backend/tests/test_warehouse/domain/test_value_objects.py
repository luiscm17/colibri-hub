import unittest
from decimal import Decimal
from uuid import UUID

from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.domain_errors import (
    InvalidBaleNumberError,
    InvalidBaleWeightError,
    InvalidDtexError,
    InvalidMaterialTypeError,
    InvalidShipmentNumberError,
)
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId
from warehouse.bales.domain.shipment_number import ShipmentNumber


class TestBaleNumber(unittest.TestCase):
    def test_valid_bale_number(self) -> None:
        bale = BaleNumber("BAL-001")
        self.assertEqual(bale.value, "BAL-001")

    def test_normalizes_to_uppercase(self) -> None:
        bale = BaleNumber("bal-001")
        self.assertEqual(bale.value, "BAL-001")

    def test_strips_whitespace(self) -> None:
        bale = BaleNumber("  bal-001  ")
        self.assertEqual(bale.value, "BAL-001")

    def test_rejects_empty_string(self) -> None:
        with self.assertRaises(InvalidBaleNumberError):
            BaleNumber("")

    def test_rejects_whitespace_only(self) -> None:
        with self.assertRaises(InvalidBaleNumberError):
            BaleNumber("   ")

    def test_rejects_too_long(self) -> None:
        with self.assertRaises(InvalidBaleNumberError):
            BaleNumber("X" * 11)

    def test_accepts_max_length(self) -> None:
        bale = BaleNumber("X" * 10)
        self.assertEqual(len(bale.value), 10)

    def test_is_frozen(self) -> None:
        bale = BaleNumber("BAL-001")
        with self.assertRaises(AttributeError):
            bale.value = "OTHER"  # type: ignore[misc]

    def test_is_hashable(self) -> None:
        bale = BaleNumber("BAL-001")
        s = {bale}
        self.assertIn(BaleNumber("BAL-001"), s)


class TestMaterialType(unittest.TestCase):
    def test_valid_material(self) -> None:
        mt = MaterialType("ALGODÓN")
        self.assertEqual(mt.value, "ALGODÓN")

    def test_normalizes_to_uppercase(self) -> None:
        mt = MaterialType("algodón")
        self.assertEqual(mt.value, "ALGODÓN")

    def test_strips_whitespace(self) -> None:
        mt = MaterialType("  alpaca  ")
        self.assertEqual(mt.value, "ALPACA")

    def test_rejects_empty(self) -> None:
        with self.assertRaises(InvalidMaterialTypeError):
            MaterialType("")

    def test_rejects_too_long(self) -> None:
        with self.assertRaises(InvalidMaterialTypeError):
            MaterialType("X" * 21)

    def test_is_frozen(self) -> None:
        mt = MaterialType("ALGODÓN")
        with self.assertRaises(AttributeError):
            mt.value = "OTRO"  # type: ignore[misc]


class TestBaleId(unittest.TestCase):
    def test_accepts_uuid(self) -> None:
        uid = UUID("12345678-1234-5678-1234-567812345678")
        bale_id = BaleId(uid)
        self.assertEqual(bale_id.value, uid)

    def test_is_frozen(self) -> None:
        bale_id = BaleId(UUID(int=1))
        with self.assertRaises(AttributeError):
            bale_id.value = UUID(int=2)  # type: ignore[misc]


class TestRawMaterialBatchId(unittest.TestCase):
    def test_accepts_uuid(self) -> None:
        uid = UUID("87654321-4321-8765-4321-876543210987")
        reception_id = RawMaterialBatchId(uid)
        self.assertEqual(reception_id.value, uid)

    def test_is_frozen(self) -> None:
        reception_id = RawMaterialBatchId(UUID(int=1))
        with self.assertRaises(AttributeError):
            reception_id.value = UUID(int=2)  # type: ignore[misc]


class TestBaleWeight(unittest.TestCase):
    def setUp(self) -> None:
        self.gross = Decimal("120.00")
        self.container = Decimal("20.00")

    def test_valid_weight(self) -> None:
        weight = BaleWeight(self.gross, self.container)
        self.assertEqual(weight.gross_kg, self.gross)
        self.assertEqual(weight.net_kg, self.gross - self.container)
        self.assertEqual(weight.container_kg, self.container)

    def test_accepts_decimal_strings_via_decimal(self) -> None:
        weight = BaleWeight(
            Decimal("150.5"),
            Decimal("20.25"),
        )
        self.assertEqual(weight.gross_kg, Decimal("150.5"))
        self.assertEqual(weight.net_kg, Decimal("130.25"))
        self.assertEqual(weight.container_kg, Decimal("20.25"))

    def test_gross_must_be_positive(self) -> None:
        with self.assertRaises(InvalidBaleWeightError):
            BaleWeight(Decimal("0"), self.container)

    def test_gross_must_be_greater_than_zero(self) -> None:
        with self.assertRaises(InvalidBaleWeightError):
            BaleWeight(Decimal("-1"), self.container)

    def test_container_must_be_positive(self) -> None:
        with self.assertRaises(InvalidBaleWeightError):
            BaleWeight(self.gross, Decimal("0"))

    def test_container_must_be_greater_than_zero(self) -> None:
        with self.assertRaises(InvalidBaleWeightError):
            BaleWeight(self.gross, Decimal("-1"))

    def test_gross_must_exceed_container(self) -> None:
        with self.assertRaises(InvalidBaleWeightError):
            BaleWeight(Decimal("90"), Decimal("100"))

    def test_rejects_nan(self) -> None:
        with self.assertRaises(InvalidBaleWeightError):
            BaleWeight(Decimal("NaN"), self.container)

    def test_rejects_infinity(self) -> None:
        with self.assertRaises(InvalidBaleWeightError):
            BaleWeight(
                Decimal("Infinity"),
                self.container,
            )

    def test_is_frozen(self) -> None:
        weight = BaleWeight(self.gross, self.container)
        with self.assertRaises(AttributeError):
            weight.gross_kg = Decimal("999")  # type: ignore[misc]


class TestShipmentNumber(unittest.TestCase):
    def test_valid_shipment_number(self) -> None:
        sn = ShipmentNumber("SHIP-001")
        self.assertEqual(sn.value, "SHIP-001")

    def test_normalizes_to_uppercase(self) -> None:
        sn = ShipmentNumber("ship-001")
        self.assertEqual(sn.value, "SHIP-001")

    def test_strips_whitespace(self) -> None:
        sn = ShipmentNumber("  ship-001  ")
        self.assertEqual(sn.value, "SHIP-001")

    def test_rejects_empty_string(self) -> None:
        with self.assertRaises(InvalidShipmentNumberError):
            ShipmentNumber("")

    def test_rejects_whitespace_only(self) -> None:
        with self.assertRaises(InvalidShipmentNumberError):
            ShipmentNumber("   ")

    def test_rejects_too_long(self) -> None:
        with self.assertRaises(InvalidShipmentNumberError):
            ShipmentNumber("X" * 11)

    def test_accepts_max_length(self) -> None:
        sn = ShipmentNumber("X" * 10)
        self.assertEqual(len(sn.value), 10)

    def test_is_frozen(self) -> None:
        sn = ShipmentNumber("SHIP-001")
        with self.assertRaises(AttributeError):
            sn.value = "OTHER"  # type: ignore[misc]

    def test_is_hashable(self) -> None:
        sn = ShipmentNumber("SHIP-001")
        s = {sn}
        self.assertIn(ShipmentNumber("SHIP-001"), s)


class TestDtex(unittest.TestCase):
    def test_valid_dtex(self) -> None:
        dtex = Dtex(Decimal("2.2"))
        self.assertEqual(dtex.value, Decimal("2.2"))

    def test_accepts_integer(self) -> None:
        dtex = Dtex(Decimal("100"))
        self.assertEqual(dtex.value, Decimal("100"))

    def test_rejects_zero(self) -> None:
        with self.assertRaises(InvalidDtexError):
            Dtex(Decimal("0"))

    def test_rejects_negative(self) -> None:
        with self.assertRaises(InvalidDtexError):
            Dtex(Decimal("-1"))

    def test_rejects_nan(self) -> None:
        with self.assertRaises(InvalidDtexError):
            Dtex(Decimal("NaN"))

    def test_rejects_infinity(self) -> None:
        with self.assertRaises(InvalidDtexError):
            Dtex(Decimal("Infinity"))

    def test_is_frozen(self) -> None:
        dtex = Dtex(Decimal("2.2"))
        with self.assertRaises(AttributeError):
            dtex.value = Decimal("999")  # type: ignore[misc]

    def test_is_hashable(self) -> None:
        dtex = Dtex(Decimal("2.2"))
        s = {dtex}
        self.assertIn(Dtex(Decimal("2.2")), s)


if __name__ == "__main__":
    unittest.main()
