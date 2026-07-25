import unittest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from infra.persistence.record_registry import RecordRegistry
from warehouse.bales.adapters.persistence.bale_record import BaleRecord
from warehouse.bales.adapters.persistence.bale_mapper import BaleMapper
from warehouse.bales.adapters.persistence.bale_repository import BaleRepository
from warehouse.bales.adapters.persistence.raw_material_batch_mapper import RawMaterialBatchMapper
from warehouse.bales.adapters.persistence.raw_material_batch_record import RawMaterialBatchRecord
from warehouse.bales.adapters.persistence.raw_material_batch_repository import RawMaterialBatchRepository
from warehouse.bales.domain.bale_id import BaleId


class TestBaleRepository(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        RecordRegistry.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self._add_reception(1, "SHIP-001")
        self._add_reception(2, "SHIP-002")
        self.session.flush()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def _add_reception(self, reception_id: int, shipment_number: str) -> None:
        self.session.add(
            RawMaterialBatchRecord(
                id=UUID(int=reception_id),
                received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                shipment_number=shipment_number,
                provider_name="Provider",
            )
        )

    def _add_bale(
        self,
        bale_id: int,
        reception_id: int,
        bale_number: str,
    ) -> None:
        self.session.add(
            BaleRecord(
                id=UUID(int=bale_id),
                reception_id=UUID(int=reception_id),
                bale_number=bale_number,
                material_type="COTTON",
                dtex=Decimal("2.2000"),
                gross_weight_kg=Decimal("120.000"),
                container_weight_kg=Decimal("20.000"),
                status="in_warehouse",
            )
        )

    def test_rejects_same_bale_number_within_reception(self) -> None:
        self._add_bale(3, 1, "BAL-001")
        self.session.commit()
        self._add_bale(4, 1, "BAL-001")

        with self.assertRaises(IntegrityError):
            self.session.commit()

    def test_allows_same_bale_number_in_different_receptions(self) -> None:
        self._add_bale(3, 1, "BAL-001")
        self._add_bale(4, 2, "BAL-001")

        self.session.commit()

        self.assertEqual(
            self.session.query(BaleRecord).count(),
            2,
        )

    def test_canonical_repositories_map_batch_then_bale(self) -> None:
        batch_id, bale_id = UUID(int=3), UUID(int=4)
        batch = RawMaterialBatchMapper.to_domain(
            RawMaterialBatchRecord(id=batch_id, received_at=datetime(2026, 1, 1, tzinfo=timezone.utc), shipment_number="SHIP-003", provider_name="Provider"),
            (BaleId(bale_id),),
        )
        bale = BaleMapper.to_domain(
            BaleRecord(id=bale_id, reception_id=batch_id, bale_number="BAL-003", material_type="COTTON", dtex=Decimal("2.2"), gross_weight_kg=Decimal("120"), container_weight_kg=Decimal("20"), status="in_warehouse")
        )

        RawMaterialBatchRepository(self.session).add(batch)
        BaleRepository(self.session).add_all((bale,))
        self.session.commit()

        self.assertEqual(self.session.get(BaleRecord, bale_id).reception_id, batch_id)


if __name__ == "__main__":
    unittest.main()
