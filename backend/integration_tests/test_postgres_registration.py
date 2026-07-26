import unittest
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.integration_tests.database_test_support import (
    cleanup_slice_six_rows,
    test_engine,
)
from warehouse.bales.adapters.persistence.bale_repository import BaleRepositoryAdapter
from warehouse.bales.adapters.persistence.raw_material_batch_repository import (
    RawMaterialBatchRepositoryAdapter,
)
from warehouse.bales.adapters.persistence.transaction import TransactionAdapter
from warehouse.bales.application.errors import (
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
)
from warehouse.bales.application.register_raw_material_batch import RegisterRawMaterialBatch
from warehouse.bales.application.register_raw_material_batch_command import (
    ReceivedBaleCommand,
    RegisterRawMaterialBatchCommand,
)


class FixedIdentityGenerator:
    def __init__(self, *identities: UUID) -> None:
        self._identities = iter(identities)

    def next_id(self) -> UUID:
        return next(self._identities)


class PostgreSQLRegistrationTests(unittest.TestCase):
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

    def test_registration_commits_batch_and_multiple_bales_atomically(self) -> None:
        batch_id, first_bale_id, second_bale_id = (UUID(int=value) for value in range(601, 604))
        result = self._use_case(batch_id, first_bale_id, second_bale_id).execute(
            self._command("S6SUCCESS", "S6BALE01", "S6BALE02")
        )

        with self.engine.connect() as connection:
            rows = connection.execute(text("SELECT shipment_number, bale_number FROM raw_material_batches JOIN raw_material_bales ON raw_material_bales.raw_material_batch_id = raw_material_batches.id WHERE raw_material_batches.id = :id ORDER BY bale_number"), {"id": batch_id}).all()
        self.assertEqual(result.raw_material_batch_id, batch_id)
        self.assertEqual(result.bale_count, 2)
        self.assertEqual([bale.status for bale in result.bales], ["in_warehouse", "in_warehouse"])
        self.assertEqual(rows, [("S6SUCCESS", "S6BALE01"), ("S6SUCCESS", "S6BALE02")])

    def test_duplicate_shipment_rolls_back_and_maps_the_database_diagnostic(self) -> None:
        self._use_case(UUID(int=610), UUID(int=611)).execute(self._command("S6DUPSHIP", "S6ONE001"))
        with self.assertRaises(DuplicateShipmentNumberError):
            self._use_case(UUID(int=612), UUID(int=613)).execute(self._command("S6DUPSHIP", "S6TWO001"))

        with self.engine.connect() as connection:
            batches, bales = connection.execute(text("SELECT count(*), (SELECT count(*) FROM raw_material_bales) FROM raw_material_batches WHERE provider_name = 'slice6-test'")).one()
        self.assertEqual((batches, bales), (1, 1))

    def test_canonical_duplicate_is_rejected_before_persistence(self) -> None:
        with self.assertRaises(DuplicateBaleNumberError):
            self._use_case(UUID(int=620), UUID(int=621), UUID(int=622)).execute(
                self._command("S6CANON", "s6same01", " S6SAME01 ")
            )

        with self.engine.connect() as connection:
            count = connection.execute(text("SELECT count(*) FROM raw_material_batches WHERE provider_name = 'slice6-test'")).scalar_one()
        self.assertEqual(count, 0)

    def test_same_canonical_bale_number_is_valid_in_distinct_batches(self) -> None:
        self._use_case(UUID(int=630), UUID(int=631)).execute(self._command("S6BATCH1", "shared01"))
        self._use_case(UUID(int=632), UUID(int=633)).execute(self._command("S6BATCH2", " SHARED01 "))

        with self.engine.connect() as connection:
            count = connection.execute(text("SELECT count(*) FROM raw_material_bales WHERE bale_number = 'SHARED01'")) .scalar_one()
        self.assertEqual(count, 2)

    def _use_case(self, *identities: UUID) -> RegisterRawMaterialBatch:
        return RegisterRawMaterialBatch(
            RawMaterialBatchRepositoryAdapter(self.session),
            BaleRepositoryAdapter(self.session),
            TransactionAdapter(self.session),
            FixedIdentityGenerator(*identities),
        )

    @staticmethod
    def _command(shipment_number: str, *bale_numbers: str) -> RegisterRawMaterialBatchCommand:
        return RegisterRawMaterialBatchCommand(
            received_at=datetime(2026, 7, 26, tzinfo=UTC), shipment_number=shipment_number,
            provider_name="slice6-test", bales=tuple(
                ReceivedBaleCommand(number, "cotton", Decimal("200"), Decimal("25"), Decimal("1"))
                for number in bale_numbers
            ),
        )
