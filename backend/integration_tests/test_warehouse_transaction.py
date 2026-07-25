import unittest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.integration_tests.database_test_support import (
    clean_warehouse_tables,
    create_test_engine,
)
from warehouse.bales.adapters.persistence.bale_record import (
    BaleRecord,
)
from warehouse.bales.adapters.persistence.raw_material_batch_record import (
    RawMaterialBatchRecord,
)
from warehouse.bales.adapters.persistence.transaction import (
    SqlAlchemyTransaction,
)
from warehouse.bales.ports import DuplicateBaleNumberConflict


class TestWarehouseTransactionIntegration(unittest.TestCase):
    engine: Engine

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_test_engine()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        clean_warehouse_tables(self.engine)

    def tearDown(self) -> None:
        clean_warehouse_tables(self.engine)

    def test_rolls_back_flushed_records_and_propagates_original_error(self) -> None:
        reception_id = uuid4()

        with Session(self.engine) as session:
            with self.assertRaisesRegex(RuntimeError, "deterministic failure"):
                with SqlAlchemyTransaction(session):
                    session.add(self._reception(reception_id, "SHIP-900"))
                    session.flush()
                    self.assertIsNotNone(
                        session.get(RawMaterialBatchRecord, reception_id)
                    )
                    raise RuntimeError("deterministic failure")

        with Session(self.engine) as read_session:
            self.assertIsNone(
                read_session.get(RawMaterialBatchRecord, reception_id)
            )
            self.assertEqual(
                read_session.scalars(
                    select(BaleRecord).where(
                        BaleRecord.raw_material_batch_id == reception_id
                    )
                ).all(),
                [],
            )

    def test_translates_composite_bale_constraint_and_rolls_back(self) -> None:
        reception_id = uuid4()
        first_bale_id = uuid4()
        second_bale_id = uuid4()

        with Session(self.engine) as session:
            with self.assertRaises(DuplicateBaleNumberConflict):
                with SqlAlchemyTransaction(session) as transaction:
                    session.add(self._reception(reception_id, "SHIP-910"))
                    session.flush()
                    session.add_all(
                        [
                            self._bale(first_bale_id, reception_id, "BAL-910"),
                            self._bale(second_bale_id, reception_id, "BAL-910"),
                        ]
                    )
                    transaction.commit()

        with Session(self.engine) as read_session:
            self.assertIsNone(
                read_session.get(RawMaterialBatchRecord, reception_id)
            )
            self.assertEqual(
                read_session.scalars(
                    select(BaleRecord).where(
                        BaleRecord.id.in_(
                            (first_bale_id, second_bale_id)
                        )
                    )
                ).all(),
                [],
            )

    @staticmethod
    def _reception(reception_id, shipment_number: str) -> RawMaterialBatchRecord:
        return RawMaterialBatchRecord(
            id=reception_id,
            received_at=datetime.now(timezone.utc),
            shipment_number=shipment_number,
            provider_name="Integration provider",
        )

    @staticmethod
    def _bale(bale_id, reception_id, bale_number: str) -> BaleRecord:
        return BaleRecord(
            id=bale_id,
            raw_material_batch_id=reception_id,
            bale_number=bale_number,
            material_type="COTTON",
            dtex=Decimal("2.2"),
            gross_weight_kg=Decimal("100.5"),
            container_weight_kg=Decimal("5.5"),
            status="in_warehouse",
        )


if __name__ == "__main__":
    unittest.main()
