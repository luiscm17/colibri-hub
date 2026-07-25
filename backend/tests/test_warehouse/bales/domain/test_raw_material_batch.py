import unittest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from warehouse.bales.domain import (
    DuplicateBaleIdError,
    EmptyRawMaterialBatchError,
    RawMaterialBatch,
)
from warehouse.bales.domain.bale import Bale
from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_status import BaleStatus
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.reception_datetime import ReceptionDateTime
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId
from warehouse.bales.domain.shipment_number import ShipmentNumber
from warehouse.domain.raw_material import BaleReception
from warehouse.domain.raw_material.bale import Bale as LegacyBale
from warehouse.domain.raw_material.bale_id import BaleId as LegacyBaleId
from warehouse.domain.raw_material.bale_number import BaleNumber as LegacyBaleNumber
from warehouse.domain.raw_material.bale_reception_id import BaleReceptionId
from warehouse.domain.raw_material.domain_errors import EmptyBaleReceptionError


class TestRawMaterialBatch(unittest.TestCase):
    def setUp(self) -> None:
        self.batch_id = RawMaterialBatchId(UUID(int=1))
        self.received_at = ReceptionDateTime(datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.bale_id = BaleId(UUID(int=2))

    def _batch(
        self,
        shipment_number: str = "ship-001",
        bale_ids: tuple[BaleId, ...] | None = None,
    ) -> RawMaterialBatch:
        return RawMaterialBatch(
            id=self.batch_id,
            received_at=self.received_at,
            shipment_number=ShipmentNumber(shipment_number),
            provider_name="  Provider  ",
            bale_ids=(self.bale_id,) if bale_ids is None else bale_ids,
        )

    def test_technical_identity_is_distinct_from_business_identity(self) -> None:
        first = self._batch()
        second = RawMaterialBatch(
            id=RawMaterialBatchId(UUID(int=3)),
            received_at=self.received_at,
            shipment_number=ShipmentNumber("SHIP-001"),
            provider_name="Other provider",
            bale_ids=(BaleId(UUID(int=4)),),
        )
        same_identity = RawMaterialBatch(
            id=self.batch_id,
            received_at=self.received_at,
            shipment_number=ShipmentNumber("SHIP-002"),
            provider_name="Other provider",
            bale_ids=(BaleId(UUID(int=4)),),
        )
        self.assertNotEqual(first, second)
        self.assertEqual(first, same_identity)
        self.assertNotEqual(first.shipment_number, same_identity.shipment_number)
        self.assertEqual(first.provider_name, "Provider")

    def test_raw_material_batch_id_is_opaque_and_immutable(self) -> None:
        self.assertEqual(self.batch_id.value, UUID(int=1))
        with self.assertRaises(AttributeError):
            self.batch_id.value = UUID(int=2)  # type: ignore[misc]

    def test_same_bale_number_is_valid_in_distinct_batches(self) -> None:
        second_batch = RawMaterialBatch(
            id=RawMaterialBatchId(UUID(int=3)),
            received_at=self.received_at,
            shipment_number=ShipmentNumber("SHIP-002"),
            provider_name="Provider",
            bale_ids=(BaleId(UUID(int=4)),),
        )
        self.assertNotEqual(self._batch("SHIP-001"), second_batch)
        self.assertEqual(BaleNumber(" bal-001 ").value, "BAL-001")

    def test_defensively_converts_and_validates_bale_ids(self) -> None:
        caller_bale_ids = [self.bale_id]
        batch = self._batch(bale_ids=caller_bale_ids)  # type: ignore[arg-type]
        caller_bale_ids.append(BaleId(UUID(int=3)))
        self.assertEqual(batch.bale_ids, (self.bale_id,))
        self.assertIsInstance(batch.bale_ids, tuple)
        with self.assertRaises(EmptyRawMaterialBatchError):
            self._batch(bale_ids=())
        with self.assertRaises(DuplicateBaleIdError):
            self._batch(bale_ids=(self.bale_id, self.bale_id))

    def test_legacy_symbols_preserve_canonical_identity(self) -> None:
        self.assertIs(BaleReception, RawMaterialBatch)
        self.assertIs(LegacyBale, Bale)
        self.assertIs(LegacyBaleId, BaleId)
        self.assertIs(LegacyBaleNumber, BaleNumber)
        self.assertIs(BaleReceptionId, RawMaterialBatchId)
        self.assertIs(EmptyBaleReceptionError, EmptyRawMaterialBatchError)

    def test_bale_p0_behavior_is_unchanged(self) -> None:
        bale = Bale(
            id=self.bale_id,
            raw_material_batch_id=self.batch_id,
            bale_number=BaleNumber("BAL-001"),
            material=MaterialType("algodón"),
            dtex=Dtex(Decimal("2.2")),
            weight=BaleWeight(Decimal("120"), Decimal("20")),
        )
        self.assertIs(bale.raw_material_batch_id, self.batch_id)
        self.assertFalse(hasattr(bale, "shipment_number"))
        self.assertIs(bale.status, BaleStatus.IN_WAREHOUSE)
        self.assertTrue(bale.is_available)
        bale.deliver()
        self.assertIs(bale.status, BaleStatus.DELIVERED)


if __name__ == "__main__":
    unittest.main()
