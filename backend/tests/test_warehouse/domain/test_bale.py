import unittest
from decimal import Decimal
from uuid import uuid4

from warehouse.bales.domain import (
    Bale,
    DomainError,
    InvalidBaleStateTransitionError,
)
from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_status import BaleStatus
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.domain_errors import (
    InvalidBaleNumberError,
    InvalidBaleWeightError,
    InvalidMaterialTypeError,
    InvalidProviderNameError,
)
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId


class TestBaleStatus(unittest.TestCase):
    def test_in_warehouse_value(self) -> None:
        self.assertEqual(BaleStatus.IN_WAREHOUSE.value, "in_warehouse")

    def test_delivered_value(self) -> None:
        self.assertEqual(BaleStatus.DELIVERED.value, "delivered")

    def test_default_is_in_warehouse(self) -> None:
        bale = self._make_bale()
        self.assertIs(bale.status, BaleStatus.IN_WAREHOUSE)

    def _make_bale(self) -> Bale:
        return Bale(
            id=BaleId(uuid4()),
            raw_material_batch_id=RawMaterialBatchId(uuid4()),
            bale_number=BaleNumber("BAL-001"),
            material=MaterialType("ALGODÓN"),
            dtex=Dtex(Decimal("2.2")),
            weight=BaleWeight(
                Decimal("120"),
                Decimal("20"),
            ),
        )


class TestBale(unittest.TestCase):
    def setUp(self) -> None:
        self.bale = Bale(
            id=BaleId(uuid4()),
            raw_material_batch_id=RawMaterialBatchId(uuid4()),
            bale_number=BaleNumber("BAL-001"),
            material=MaterialType("ALGODÓN"),
            dtex=Dtex(Decimal("2.2")),
            weight=BaleWeight(
                Decimal("120"),
                Decimal("20"),
            ),
        )

    def test_initial_status_is_in_warehouse(self) -> None:
        self.assertIs(self.bale.status, BaleStatus.IN_WAREHOUSE)

    def test_is_available_when_in_warehouse(self) -> None:
        self.assertTrue(self.bale.is_available)

    def test_is_not_available_after_delivery(self) -> None:
        self.bale.deliver()
        self.assertFalse(self.bale.is_available)

    def test_delivered_changes_status(self) -> None:
        self.bale.deliver()
        self.assertIs(self.bale.status, BaleStatus.DELIVERED)

    def test_delivered_twice_raises_error(self) -> None:
        self.bale.deliver()
        with self.assertRaises(InvalidBaleStateTransitionError) as ctx:
            self.bale.deliver()
        self.assertIn("BAL-001", str(ctx.exception))

    def test_delivered_on_pre_delivered_raises_error(self) -> None:
        self.bale.deliver()
        with self.assertRaises(InvalidBaleStateTransitionError):
            self.bale.deliver()

    def test_uses_slots(self) -> None:
        with self.assertRaises(AttributeError):
            self.bale.non_existent = "x"  # type: ignore[attr-defined]

    def test_repr_includes_bale_number(self) -> None:
        representation = repr(self.bale)
        self.assertIn("BAL-001", representation)


class TestDomainExceptions(unittest.TestCase):
    def test_domain_errors_is_base(self) -> None:
        self.assertTrue(issubclass(InvalidBaleNumberError, DomainError))
        self.assertTrue(issubclass(InvalidMaterialTypeError, DomainError))
        self.assertTrue(issubclass(InvalidBaleWeightError, DomainError))
        self.assertTrue(issubclass(InvalidBaleStateTransitionError, DomainError))
        self.assertTrue(issubclass(InvalidProviderNameError, DomainError))

    def test_invalid_bale_number_error_message(self) -> None:
        err = InvalidBaleNumberError("test message")
        self.assertEqual(str(err), "test message")

    def test_invalid_state_transition_message(self) -> None:
        err = InvalidBaleStateTransitionError(
            "Bale BAL-001 is not available in warehouse."
        )
        self.assertIn("BAL-001", str(err))


if __name__ == "__main__":
    unittest.main()
