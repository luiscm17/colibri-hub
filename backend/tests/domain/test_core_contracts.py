from datetime import datetime
from decimal import Decimal
import unittest

from warehouse.bales.domain.bale import Bale
from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_status import BaleStatus
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.raw_material_batch import RawMaterialBatch
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId
from warehouse.bales.domain.reception_datetime import ReceptionDateTime
from warehouse.bales.domain.shipment_number import ShipmentNumber
from warehouse.bales.domain.domain_errors import (
    DuplicateBaleIdError,
    EmptyRawMaterialBatchError,
    InvalidBaleNumberError,
    InvalidBaleStateTransitionError,
    InvalidBaleWeightError,
    InvalidDtexError,
    InvalidReceptionDateTimeError,
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
    def test_value_objects_normalize_and_reject_representative_invalid_values(self) -> None:
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
        weight = BaleWeight(GROSS_WEIGHT_KG, CONTAINER_WEIGHT_KG)
        self.assertEqual(weight.net_kg, Decimal("25.0"))
        with self.assertRaises(InvalidBaleWeightError):
            BaleWeight(Decimal("1"), Decimal("1"))
        self.assertEqual(ReceptionDateTime(RECEIVED_AT).value, RECEIVED_AT)
        with self.assertRaises(InvalidReceptionDateTimeError):
            ReceptionDateTime(datetime(2026, 7, 25, 10, 30))

    def test_bale_delivery_changes_availability_once(self) -> None:
        bale = self._bale()
        self.assertTrue(bale.is_available)
        bale.deliver()
        self.assertEqual(bale.status, BaleStatus.DELIVERED)
        self.assertFalse(bale.is_available)
        with self.assertRaises(InvalidBaleStateTransitionError):
            bale.deliver()

    def test_batch_identity_and_bale_id_invariants(self) -> None:
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
        return Bale(
            id=BaleId(BALE_ID_1), raw_material_batch_id=RawMaterialBatchId(BATCH_ID),
            bale_number=BaleNumber("bale-01"), material=MaterialType("cotton"),
            dtex=Dtex(DTEX), weight=BaleWeight(GROSS_WEIGHT_KG, CONTAINER_WEIGHT_KG),
        )

    @staticmethod
    def _batch(bale_ids: tuple[BaleId, ...], identifier=BATCH_ID) -> RawMaterialBatch:
        return RawMaterialBatch(
            id=RawMaterialBatchId(identifier), received_at=ReceptionDateTime(RECEIVED_AT),
            shipment_number=ShipmentNumber("ship-01"), provider_name=" Fiber Supplier ",
            bale_ids=bale_ids,
        )
