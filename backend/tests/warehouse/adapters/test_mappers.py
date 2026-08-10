import unittest
from datetime import date
from typing import cast

from sqlalchemy import Date, Numeric, String, Table, Text
from warehouse.bales.adapters.persistence.bale_mapper import BaleMapper
from warehouse.bales.adapters.persistence.bale_record import BaleRecord
from warehouse.bales.adapters.persistence.raw_material_batch_mapper import (
    RawMaterialBatchMapper,
)
from warehouse.bales.adapters.persistence.raw_material_batch_record import (
    RawMaterialBatchRecord,
)
from warehouse.bales.domain.bale import Bale
from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.delivery_date import DeliveryDate
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.raw_material_batch import RawMaterialBatch
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId
from warehouse.bales.domain.reception_date import ReceptionDate
from warehouse.bales.domain.shipment_number import ShipmentNumber

from backend.tests.support.values import (
    BALE_ID_1,
    BALE_ID_2,
    BATCH_ID,
    CONTAINER_WEIGHT_KG,
    DTEX,
    GROSS_WEIGHT_KG,
    RECEIVED_AT,
)


class PersistenceMapperTest(unittest.TestCase):
    """ORM mapper contracts: dialect-neutral metadata and round-trip preservation of domain values."""

    def test_records_expose_dialect_neutral_table_column_metadata(self) -> None:
        """Table and column metadata are dialect-neutral and match the expected schema."""
        self.assertEqual(cast(Table, RawMaterialBatchRecord.__table__).name, "raw_material_batches")
        self.assertEqual(cast(Table, BaleRecord.__table__).name, "raw_material_bales")

        batch_columns = RawMaterialBatchRecord.__table__.c
        self.assertIsInstance(batch_columns.received_at.type, Date)
        self.assertIsInstance(batch_columns.shipment_number.type, String)
        self.assertEqual(cast(String, batch_columns.shipment_number.type).length, 10)
        self.assertIsInstance(batch_columns.provider_name.type, Text)
        self.assertFalse(batch_columns.provider_name.nullable)

        bale_columns = BaleRecord.__table__.c
        self.assertEqual(bale_columns.raw_material_batch_id.nullable, False)
        self.assertEqual(cast(String, bale_columns.bale_number.type).length, 10)
        self.assertEqual(cast(String, bale_columns.material_type.type).length, 20)
        self.assertEqual(cast(String, bale_columns.status.type).length, 40)
        for column in ("dtex", "gross_weight_kg", "container_weight_kg"):
            self.assertIsInstance(bale_columns[column].type, Numeric)
            self.assertFalse(bale_columns[column].nullable)

    def test_raw_material_batch_mapper_preserves_identity_values_and_bale_order(self) -> None:
        """Batch mapper round-trips identity fields and preserves bale ID ordering."""
        batch = RawMaterialBatch(
            id=RawMaterialBatchId(BATCH_ID),
            received_at=ReceptionDate(RECEIVED_AT),
            shipment_number=ShipmentNumber("ship-01"),
            provider_name="Fiber Supplier",
            bale_ids=(BaleId(BALE_ID_1), BaleId(BALE_ID_2)),
        )

        record = RawMaterialBatchMapper.to_record(batch)
        restored = RawMaterialBatchMapper.to_domain(record, batch.bale_ids)

        self.assertEqual(record.id, BATCH_ID)
        self.assertEqual(record.received_at, RECEIVED_AT)
        self.assertEqual(record.shipment_number, "SHIP-01")
        self.assertEqual(record.provider_name, "Fiber Supplier")
        self.assertEqual(restored, batch)
        self.assertEqual(restored.bale_ids, batch.bale_ids)

    def test_bale_mapper_preserves_decimal_values_and_delivered_status(self) -> None:
        """Bale mapper round-trips Decimal values and preserves the delivered status."""
        delivery_date = DeliveryDate(date(2026, 8, 1))
        bale = Bale(
            id=BaleId(BALE_ID_1),
            raw_material_batch_id=RawMaterialBatchId(BATCH_ID),
            bale_number=BaleNumber("bale-01"),
            material=MaterialType("cotton"),
            dtex=Dtex(DTEX),
            weight=BaleWeight(GROSS_WEIGHT_KG, CONTAINER_WEIGHT_KG),
        )
        bale.deliver(delivery_date)

        record = BaleMapper.to_record(bale)
        restored = BaleMapper.to_domain(record)

        self.assertEqual(record.id, BALE_ID_1)
        self.assertEqual(record.raw_material_batch_id, BATCH_ID)
        self.assertEqual(record.bale_number, "BALE-01")
        self.assertEqual(record.dtex, DTEX)
        self.assertEqual(record.gross_weight_kg, GROSS_WEIGHT_KG)
        self.assertEqual(record.container_weight_kg, CONTAINER_WEIGHT_KG)
        self.assertEqual(record.status, "delivered")
        self.assertEqual(restored.status, bale.status)
        self.assertEqual(restored.weight, bale.weight)
