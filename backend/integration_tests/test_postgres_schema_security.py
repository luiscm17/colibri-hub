import os
import unittest
from unittest.mock import patch

from sqlalchemy import text

from backend.integration_tests.database_test_support import test_engine, validated_test_database_url


class PostgreSQLSchemaSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = test_engine()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def test_guard_requires_the_explicit_local_psycopg_target(self) -> None:
        valid_url = "postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres"
        with patch.dict(os.environ, {"TEST_DATABASE_URL": valid_url}, clear=True):
            self.assertEqual(validated_test_database_url(), valid_url)

        for unsafe_url in (None, "postgresql://postgres@127.0.0.1:54322/postgres", "postgresql+psycopg://postgres@db:54322/postgres", "postgresql+psycopg://postgres@127.0.0.1:5432/postgres", "postgresql+psycopg://postgres@127.0.0.1:54322/other"):
            with self.subTest(unsafe_url=unsafe_url), patch.dict(os.environ, {}, clear=True):
                if unsafe_url is not None:
                    os.environ["TEST_DATABASE_URL"] = unsafe_url
                with self.assertRaisesRegex(RuntimeError, "TEST_DATABASE_URL"):
                    validated_test_database_url()

    def test_schema_constraints_and_index_match_the_current_migration(self) -> None:
        with self.engine.connect() as connection:
            columns = connection.execute(text("SELECT table_name, column_name, data_type, character_maximum_length, is_nullable, column_default FROM information_schema.columns WHERE table_schema = 'public' AND table_name IN ('raw_material_batches', 'raw_material_bales') ORDER BY table_name, ordinal_position")).all()
            constraints = dict(connection.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid IN ('public.raw_material_batches'::regclass, 'public.raw_material_bales'::regclass)")).all())
            indexes = dict(connection.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' AND indexname IN ('ix_raw_material_bales_raw_material_batch_id', 'ix_raw_material_bales_status', 'ix_raw_material_batches_received_at', 'ix_raw_material_bales_material_type')")).all())

        self.assertEqual(columns, [
            ("raw_material_bales", "id", "uuid", None, "NO", None),
            ("raw_material_bales", "raw_material_batch_id", "uuid", None, "NO", None),
            ("raw_material_bales", "bale_number", "character varying", 10, "NO", None),
            ("raw_material_bales", "material_type", "character varying", 20, "NO", None),
            ("raw_material_bales", "dtex", "numeric", None, "NO", None),
            ("raw_material_bales", "gross_weight_kg", "numeric", None, "NO", None),
            ("raw_material_bales", "container_weight_kg", "numeric", None, "NO", None),
            ("raw_material_bales", "status", "character varying", 40, "NO", None),
            ("raw_material_bales", "delivery_date", "date", None, "YES", None),
            ("raw_material_batches", "id", "uuid", None, "NO", None),
            ("raw_material_batches", "received_at", "date", None, "NO", None),
            ("raw_material_batches", "shipment_number", "character varying", 10, "NO", None),
            ("raw_material_batches", "provider_name", "text", None, "NO", None),
        ])
        self.assertIn("PRIMARY KEY (id)", constraints["pk_raw_material_batches"])
        self.assertIn("UNIQUE (shipment_number)", constraints["uq_raw_material_batches_shipment_number"])
        self.assertIn("PRIMARY KEY (id)", constraints["pk_raw_material_bales"])
        self.assertIn("FOREIGN KEY (raw_material_batch_id) REFERENCES raw_material_batches(id) ON DELETE RESTRICT", constraints["fk_raw_material_bales_raw_material_batch_id"])
        self.assertIn("UNIQUE (raw_material_batch_id, bale_number)", constraints["uq_raw_material_bales_raw_material_batch_bale_number"])
        self.assertIn("CHECK", constraints["ck_raw_material_bales_status"])
        self.assertIn("in_warehouse", constraints["ck_raw_material_bales_status"])
        self.assertIn("delivered", constraints["ck_raw_material_bales_status"])
        self.assertIn("in_warehouse", constraints["ck_raw_material_bales_status_delivery_date"])
        self.assertIn("delivery_date IS NULL", constraints["ck_raw_material_bales_status_delivery_date"])
        self.assertIn("delivered", constraints["ck_raw_material_bales_status_delivery_date"])
        self.assertIn("delivery_date IS NOT NULL", constraints["ck_raw_material_bales_status_delivery_date"])
        self.assertIn("(raw_material_batch_id)", indexes["ix_raw_material_bales_raw_material_batch_id"])
        self.assertIn("(status)", indexes["ix_raw_material_bales_status"])
        self.assertIn("(received_at)", indexes["ix_raw_material_batches_received_at"])
        self.assertIn("(material_type)", indexes["ix_raw_material_bales_material_type"])

    def test_rls_has_no_policies_and_application_roles_have_no_table_privileges(self) -> None:
        with self.engine.connect() as connection:
            rls = connection.execute(text("SELECT relname, relrowsecurity FROM pg_class WHERE oid IN ('public.raw_material_batches'::regclass, 'public.raw_material_bales'::regclass) ORDER BY relname")).all()
            policy_count = connection.execute(text("SELECT count(*) FROM pg_policies WHERE schemaname = 'public' AND tablename IN ('raw_material_batches', 'raw_material_bales')")).scalar_one()
            privileges = connection.execute(text("SELECT role_name, table_name, has_table_privilege(role_name, 'public.' || table_name, privilege) FROM (VALUES ('anon'), ('authenticated'), ('service_role')) AS roles(role_name) CROSS JOIN (VALUES ('raw_material_batches'), ('raw_material_bales')) AS tables(table_name) CROSS JOIN (VALUES ('SELECT'), ('INSERT'), ('UPDATE'), ('DELETE')) AS actions(privilege) ORDER BY role_name, table_name, privilege")).all()

        self.assertEqual(rls, [("raw_material_bales", True), ("raw_material_batches", True)])
        self.assertEqual(policy_count, 0)
        self.assertTrue(all(not granted for _, _, granted in privileges))
