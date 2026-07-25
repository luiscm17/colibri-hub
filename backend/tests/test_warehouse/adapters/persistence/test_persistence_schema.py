import unittest

from sqlalchemy import CheckConstraint, DateTime, Numeric, String, Text

from warehouse.bales.adapters.persistence.bale_record import BaleRecord
from warehouse.bales.adapters.persistence.raw_material_batch_record import RawMaterialBatchRecord


class TestPersistenceSchema(unittest.TestCase):
    def test_domain_bounded_strings_match_domain_limits(self) -> None:
        bale_number = BaleRecord.__table__.c.bale_number.type
        material_type = BaleRecord.__table__.c.material_type.type
        shipment_number = (
            RawMaterialBatchRecord.__table__.c.shipment_number.type
        )

        self.assertIsInstance(bale_number, String)
        self.assertEqual(bale_number.length, 10)
        self.assertIsInstance(material_type, String)
        self.assertEqual(material_type.length, 20)
        self.assertIsInstance(shipment_number, String)
        self.assertEqual(shipment_number.length, 10)

    def test_shipment_number_has_named_global_unique_constraint(self) -> None:
        constraint = next(
            constraint
            for constraint in RawMaterialBatchRecord.__table__.constraints
            if constraint.name
            == "uq_raw_material_batches_shipment_number"
        )

        self.assertEqual(
            tuple(column.name for column in constraint.columns),
            ("shipment_number",),
        )

    def test_bale_number_is_unique_within_batch(self) -> None:
        constraint = next(
            constraint
            for constraint in BaleRecord.__table__.constraints
            if constraint.name
            == "uq_raw_material_bales_raw_material_batch_bale_number"
        )

        self.assertEqual(
            tuple(column.name for column in constraint.columns),
            ("raw_material_batch_id", "bale_number"),
        )

    def test_batch_id_remains_indexed_without_defaults(self) -> None:
        raw_material_batch_id = BaleRecord.__table__.c.raw_material_batch_id

        index = next(
            index
            for index in BaleRecord.__table__.indexes
            if index.name == "ix_raw_material_bales_raw_material_batch_id"
        )
        self.assertEqual(
            tuple(column.name for column in index.columns),
            ("raw_material_batch_id",),
        )
        self.assertIsNone(raw_material_batch_id.default)
        self.assertIsNone(raw_material_batch_id.server_default)

    def test_bale_status_has_named_lifecycle_check_constraint(self) -> None:
        constraint = next(
            constraint
            for constraint in BaleRecord.__table__.constraints
            if isinstance(constraint, CheckConstraint)
        )

        self.assertEqual(constraint.name, "ck_raw_material_bales_status")
        self.assertEqual(
            str(constraint.sqltext),
            "status IN ('in_warehouse', 'delivered')",
        )

    def test_provider_name_is_unbounded(self) -> None:
        provider_name = RawMaterialBatchRecord.__table__.c.provider_name.type

        self.assertIsInstance(provider_name, Text)

    def test_decimals_have_no_unconfirmed_precision_or_scale(self) -> None:
        for column_name in (
            "dtex",
            "gross_weight_kg",
            "container_weight_kg",
        ):
            numeric = BaleRecord.__table__.c[column_name].type
            self.assertIsInstance(numeric, Numeric)
            self.assertIsNone(numeric.precision)
            self.assertIsNone(numeric.scale)

    def test_reception_datetime_remains_timezone_aware(self) -> None:
        received_at = RawMaterialBatchRecord.__table__.c.received_at.type

        self.assertIsInstance(received_at, DateTime)
        self.assertTrue(received_at.timezone)


if __name__ == "__main__":
    unittest.main()
