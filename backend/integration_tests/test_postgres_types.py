import unittest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import text

from backend.integration_tests.database_test_support import cleanup_slice_five_rows, test_engine


class PostgreSQLTypeRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = test_engine()

    @classmethod
    def tearDownClass(cls) -> None:
        cleanup_slice_five_rows(cls.engine)
        cls.engine.dispose()

    def setUp(self) -> None:
        cleanup_slice_five_rows(self.engine)

    def test_aware_timestamp_and_decimals_round_trip_through_postgresql(self) -> None:
        batch_id, bale_id = uuid4(), uuid4()
        shipment_number = f"S5{batch_id.hex[:8].upper()}"
        bale_number = f"S5{bale_id.hex[:8].upper()}"
        received_at = datetime(2026, 7, 25, 15, 30, tzinfo=timezone.utc)
        with self.engine.begin() as connection:
            connection.execute(text("INSERT INTO raw_material_batches (id, received_at, shipment_number, provider_name) VALUES (:id, :received_at, :shipment_number, 'slice5-test')"), {"id": batch_id, "received_at": received_at, "shipment_number": shipment_number})
            connection.execute(text("INSERT INTO raw_material_bales (id, raw_material_batch_id, bale_number, material_type, dtex, gross_weight_kg, container_weight_kg, status) VALUES (:id, :batch_id, :bale_number, 'COTTON', :dtex, :gross_weight_kg, :container_weight_kg, 'in_warehouse')"), {"id": bale_id, "batch_id": batch_id, "bale_number": bale_number, "dtex": Decimal("167.25"), "gross_weight_kg": Decimal("42.75"), "container_weight_kg": Decimal("0.25")})
            row = connection.execute(text("SELECT received_at, dtex, gross_weight_kg, container_weight_kg FROM raw_material_batches JOIN raw_material_bales ON raw_material_bales.raw_material_batch_id = raw_material_batches.id WHERE raw_material_batches.id = :id"), {"id": batch_id}).one()

        self.assertEqual(row, (received_at, Decimal("167.25"), Decimal("42.75"), Decimal("0.25")))
