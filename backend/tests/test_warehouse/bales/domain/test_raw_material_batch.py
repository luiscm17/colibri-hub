import unittest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from uuid import uuid4

from warehouse.bales.domain import (
    DomainError,
    DuplicateBaleIdError,
    EmptyRawMaterialBatchError,
    InvalidProviderNameError,
    RawMaterialBatch,
    RawMaterialBatchId,
)
from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale import Bale
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_status import BaleStatus
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.reception_datetime import ReceptionDateTime
from warehouse.bales.domain.shipment_number import ShipmentNumber


class TestRawMaterialBatch(unittest.TestCase):
    def setUp(self) -> None:
        self.reception_id = RawMaterialBatchId(uuid4())
        self.received_at = ReceptionDateTime(datetime.now(timezone.utc))
        self.shipment_number = ShipmentNumber("SHIP-001")
        self.bale_id_1 = BaleId(uuid4())
        self.bale_id_2 = BaleId(uuid4())

    def _make_batch(
        self,
        bale_ids: tuple[BaleId, ...] | None = None,
    ) -> RawMaterialBatch:
        return RawMaterialBatch(
            id=self.reception_id,
            received_at=self.received_at,
            shipment_number=self.shipment_number,
            provider_name="PROV-001",
            bale_ids=(self.bale_id_1, self.bale_id_2) if bale_ids is None else bale_ids,
        )

    def test_creates_with_multiple_bales(self) -> None:
        batch = self._make_batch()
        self.assertEqual(batch.id, self.reception_id)
        self.assertEqual(batch.shipment_number.value, "SHIP-001")
        self.assertEqual(batch.provider_name, "PROV-001")
        self.assertEqual(len(batch.bale_ids), 2)

    def test_creates_with_single_bale(self) -> None:
        batch = self._make_batch(bale_ids=(self.bale_id_1,))
        self.assertEqual(batch.bale_count, 1)

    def test_bale_count_matches_number_of_bales(self) -> None:
        batch = self._make_batch()
        self.assertEqual(batch.bale_count, 2)

    def test_rejects_empty_bale_ids(self) -> None:
        with self.assertRaises(EmptyRawMaterialBatchError) as ctx:
            self._make_batch(bale_ids=())
        self.assertIn("at least one bale", str(ctx.exception))

    def test_rejects_duplicate_bale_ids(self) -> None:
        with self.assertRaises(DuplicateBaleIdError) as ctx:
            self._make_batch(bale_ids=(self.bale_id_1, self.bale_id_1))
        self.assertIn("duplicate", str(ctx.exception))

    def test_strips_provider_name_whitespace(self) -> None:
        reception = RawMaterialBatch(
            id=self.reception_id,
            received_at=self.received_at,
            shipment_number=self.shipment_number,
            provider_name="  PROV-001  ",
            bale_ids=(self.bale_id_1,),
        )
        self.assertEqual(reception.provider_name, "PROV-001")

    def test_rejects_empty_provider_name(self) -> None:
        with self.assertRaises(InvalidProviderNameError) as ctx:
            RawMaterialBatch(
                id=self.reception_id,
                received_at=self.received_at,
                shipment_number=self.shipment_number,
                provider_name="",
                bale_ids=(self.bale_id_1,),
            )
        self.assertIn("empty", str(ctx.exception))

    def test_rejects_whitespace_only_provider_name(self) -> None:
        with self.assertRaises(InvalidProviderNameError):
            RawMaterialBatch(
                id=self.reception_id,
                received_at=self.received_at,
                shipment_number=self.shipment_number,
                provider_name="   ",
                bale_ids=(self.bale_id_1,),
            )

    def test_is_frozen(self) -> None:
        batch = self._make_batch()
        with self.assertRaises(AttributeError):
            batch.provider_name = "OTHER"  # type: ignore[misc]

    def test_all_exceptions_inherit_from_domain_error(self) -> None:
        self.assertTrue(issubclass(EmptyRawMaterialBatchError, DomainError))
        self.assertTrue(issubclass(DuplicateBaleIdError, DomainError))
        self.assertTrue(issubclass(InvalidProviderNameError, DomainError))


class TestRawMaterialBatchIdentity(unittest.TestCase):
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
            id=RawMaterialBatchId(UUID(int=3)), received_at=self.received_at,
            shipment_number=ShipmentNumber("SHIP-001"), provider_name="Other provider",
            bale_ids=(BaleId(UUID(int=4)),),
        )
        same_identity = RawMaterialBatch(
            id=self.batch_id, received_at=self.received_at,
            shipment_number=ShipmentNumber("SHIP-002"), provider_name="Other provider",
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
            id=RawMaterialBatchId(UUID(int=3)), received_at=self.received_at,
            shipment_number=ShipmentNumber("SHIP-002"), provider_name="Provider",
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

    def test_bale_p0_behavior_is_unchanged(self) -> None:
        bale = Bale(
            id=self.bale_id, raw_material_batch_id=self.batch_id,
            bale_number=BaleNumber("BAL-001"), material=MaterialType("algodón"),
            dtex=Dtex(Decimal("2.2")), weight=BaleWeight(Decimal("120"), Decimal("20")),
        )
        self.assertIs(bale.raw_material_batch_id, self.batch_id)
        self.assertFalse(hasattr(bale, "shipment_number"))
        self.assertIs(bale.status, BaleStatus.IN_WAREHOUSE)
        self.assertTrue(bale.is_available)
        bale.deliver()
        self.assertIs(bale.status, BaleStatus.DELIVERED)


if __name__ == "__main__":
    unittest.main()
