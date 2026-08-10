from datetime import date, datetime
from decimal import Decimal
import unittest

from warehouse.bales.domain.bale import Bale
from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_status import BaleStatus
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.delivery_date import DeliveryDate
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.raw_material_batch import RawMaterialBatch
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId
from warehouse.bales.domain.reception_date import ReceptionDate
from warehouse.bales.domain.shipment_number import ShipmentNumber
from warehouse.bales.domain.domain_errors import (
    DuplicateBaleIdError,
    EmptyRawMaterialBatchError,
    InvalidBaleNumberError,
    InvalidBaleStateTransitionError,
    InvalidBaleWeightError,
    InvalidDtexError,
    InvalidReceptionDateError,
)

from backend.tests.support.values import (
    BALE_ID_1,
    BALE_ID_2,
    BATCH_ID,
    CONTAINER_WEIGHT_KG,
    DTEX,
    GROSS_WEIGHT_KG,
    RECEIVED_AT,
)


class CoreDomainContractsTest(unittest.TestCase):
    """Domain value-object contracts: normalization, boundary validation, and state transitions."""

    def test_value_objects_normalize_and_reject_representative_invalid_values(self) -> None:
        """Value objects normalize input and raise domain errors for invalid values."""
        for factory, value, expected in (
            (BaleNumber, " bale-01 ", "BALE-01"),
            (ShipmentNumber, " ship-01 ", "SHIP-01"),
            (MaterialType, " cotton ", "COTTON"),
        ):
            with self.subTest(factory=factory.__name__):
                self.assertEqual(factory(value).value, expected)
        with self.assertRaises(InvalidBaleNumberError):
            BaleNumber(" ")
        with self.assertRaises(InvalidDtexError):
            Dtex(Decimal("0"))

    def test_weight_and_reception_boundaries(self) -> None:
        """BaleWeight computes net weight and rejects equal gross/container; ReceptionDate validates date-only input."""
        weight = BaleWeight(GROSS_WEIGHT_KG, CONTAINER_WEIGHT_KG)
        self.assertEqual(weight.net_kg, Decimal("25.0"))
        with self.assertRaises(InvalidBaleWeightError):
            BaleWeight(Decimal("1"), Decimal("1"))
        self.assertEqual(ReceptionDate(RECEIVED_AT).value, RECEIVED_AT)
        with self.assertRaises(InvalidReceptionDateError):
            ReceptionDate(datetime(2026, 7, 25, 10, 30))

    def test_bale_delivery_changes_availability_once(self) -> None:
        """Delivering a bale transitions its status and marks it unavailable; a second delivery is rejected."""
        bale = self._bale()
        delivery_date = DeliveryDate(date(2026, 8, 1))
        self.assertTrue(bale.is_available)
        bale.deliver(delivery_date)
        self.assertEqual(bale.status, BaleStatus.DELIVERED)
        self.assertEqual(bale.delivery_date, delivery_date)
        self.assertFalse(bale.is_available)
        with self.assertRaises(InvalidBaleStateTransitionError):
            bale.deliver(delivery_date)

    def test_batch_identity_and_bale_id_invariants(self) -> None:
        """RawMaterialBatch enforces identity via provider/data equality, rejects empty or duplicate bale IDs."""
        batch = self._batch((BaleId(BALE_ID_1), BaleId(BALE_ID_2)))
        self.assertEqual(batch.provider_name, "Fiber Supplier")
        self.assertEqual(batch.bale_count, 2)
        self.assertEqual(batch, self._batch((BaleId(BALE_ID_1),), BATCH_ID))
        with self.assertRaises(EmptyRawMaterialBatchError):
            self._batch(())
        with self.assertRaises(DuplicateBaleIdError):
            self._batch((BaleId(BALE_ID_1), BaleId(BALE_ID_1)))

    @staticmethod
    def _bale() -> Bale:
        """Build a standard Bale instance for test reuse."""
        return Bale(
            id=BaleId(BALE_ID_1), raw_material_batch_id=RawMaterialBatchId(BATCH_ID),
            bale_number=BaleNumber("bale-01"), material=MaterialType("cotton"),
            dtex=Dtex(DTEX), weight=BaleWeight(GROSS_WEIGHT_KG, CONTAINER_WEIGHT_KG),
        )

    @staticmethod
    def _batch(bale_ids: tuple[BaleId, ...], identifier=BATCH_ID) -> RawMaterialBatch:
        """Build a RawMaterialBatch with the given bale IDs and optional custom identifier."""
        return RawMaterialBatch(
            id=RawMaterialBatchId(identifier), received_at=ReceptionDate(RECEIVED_AT),
            shipment_number=ShipmentNumber("ship-01"), provider_name=" Fiber Supplier ",
            bale_ids=bale_ids,
        )
