import unittest
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.integration_tests.database_test_support import (
    cleanup_slice_six_rows,
    test_engine,
)
from warehouse.bales.adapters.persistence.bale_record import BaleRecord
from warehouse.bales.adapters.persistence.raw_material_batch_record import RawMaterialBatchRecord
from warehouse.bales.adapters.persistence.transaction import TransactionAdapter
from warehouse.bales.ports import (
    DuplicateBaleNumberConflict,
    DuplicateShipmentNumberConflict,
)


class PostgreSQLTransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = test_engine()

    @classmethod
    def tearDownClass(cls) -> None:
        cleanup_slice_six_rows(cls.engine)
        cls.engine.dispose()

    def setUp(self) -> None:
        cleanup_slice_six_rows(self.engine)
        self.session = Session(self.engine)

    def tearDown(self) -> None:
        self.session.close()

    def test_named_unique_diagnostics_map_to_application_ports(self) -> None:
        batch_id = self._insert_batch("S6SHIP001")
        self._insert_bale(batch_id, "S6BALE001")

        self.session.add(self._batch("S6SHIP001"))
        with self.assertRaises(DuplicateShipmentNumberConflict):
            with TransactionAdapter(self.session) as transaction:
                transaction.commit()

        self.session.add(self._bale(batch_id, "S6BALE001"))
        with self.assertRaises(DuplicateBaleNumberConflict):
            with TransactionAdapter(self.session) as transaction:
                transaction.commit()

    def test_unknown_check_failure_propagates_and_rolls_back(self) -> None:
        batch_id = self._insert_batch("S6CHECK01")
        self.session.add(self._bale(batch_id, "S6CHECK01", status="invalid"))

        with self.assertRaises(IntegrityError):
            with TransactionAdapter(self.session) as transaction:
                transaction.commit()

        with self.engine.connect() as connection:
            count = connection.execute(
                text("SELECT count(*) FROM raw_material_bales WHERE raw_material_batch_id = :id"),
                {"id": batch_id},
            ).scalar_one()
        self.assertEqual(count, 0)

    def test_context_exception_rolls_back_pending_work(self) -> None:
        batch = self._batch("S6ROLL001")
        with self.assertRaisesRegex(RuntimeError, "abort"):
            with TransactionAdapter(self.session):
                self.session.add(batch)
                raise RuntimeError("abort")

        with self.engine.connect() as connection:
            count = connection.execute(
                text("SELECT count(*) FROM raw_material_batches WHERE id = :id"),
                {"id": batch.id},
            ).scalar_one()
        self.assertEqual(count, 0)

    def _insert_batch(self, shipment_number: str):
        batch = self._batch(shipment_number)
        with self.engine.begin() as connection:
            connection.execute(
                text("INSERT INTO raw_material_batches (id, received_at, shipment_number, provider_name) VALUES (:id, :received_at, :shipment_number, :provider_name)"),
                {"id": batch.id, "received_at": batch.received_at, "shipment_number": batch.shipment_number, "provider_name": batch.provider_name},
            )
        return batch.id

    def _insert_bale(self, batch_id, bale_number: str) -> None:
        bale = self._bale(batch_id, bale_number)
        with self.engine.begin() as connection:
            connection.execute(
                text("INSERT INTO raw_material_bales (id, raw_material_batch_id, bale_number, material_type, dtex, gross_weight_kg, container_weight_kg, status) VALUES (:id, :batch_id, :bale_number, :material_type, :dtex, :gross_weight_kg, :container_weight_kg, :status)"),
                {"id": bale.id, "batch_id": bale.raw_material_batch_id, "bale_number": bale.bale_number, "material_type": bale.material_type, "dtex": bale.dtex, "gross_weight_kg": bale.gross_weight_kg, "container_weight_kg": bale.container_weight_kg, "status": bale.status},
            )

    @staticmethod
    def _batch(shipment_number: str) -> RawMaterialBatchRecord:
        return RawMaterialBatchRecord(id=uuid4(), received_at=datetime(2026, 7, 26, tzinfo=UTC), shipment_number=shipment_number, provider_name="slice6-test")

    @staticmethod
    def _bale(batch_id, bale_number: str, status: str = "in_warehouse") -> BaleRecord:
        return BaleRecord(id=uuid4(), raw_material_batch_id=batch_id, bale_number=bale_number, material_type="COTTON", dtex=200, gross_weight_kg=25, container_weight_kg=1, status=status)
