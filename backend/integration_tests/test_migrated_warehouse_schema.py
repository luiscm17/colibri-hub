import unittest
from uuid import uuid4

from sqlalchemy import Numeric, Text, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID, VARCHAR
from sqlalchemy.engine import Engine

from backend.integration_tests.database_test_support import create_test_engine

TABLES = ("raw_material_batches", "raw_material_bales")


class TestMigratedWarehouseSchema(unittest.TestCase):
    engine: Engine

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_test_engine()

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "engine"):
            cls.engine.dispose()

    def test_required_tables_exist(self) -> None:
        table_names = set(inspect(self.engine).get_table_names(schema="public"))

        self.assertTrue(set(TABLES).issubset(table_names))

    def test_batch_columns_match_migration(self) -> None:
        self._assert_columns(
            "raw_material_batches",
            {
                "id": (UUID, None),
                "received_at": (TIMESTAMP, None),
                "shipment_number": (VARCHAR, 10),
                "provider_name": (Text, None),
            },
        )
        received_at = self._columns("raw_material_batches")["received_at"]
        self.assertTrue(received_at["type"].timezone)

    def test_bale_columns_match_migration(self) -> None:
        self._assert_columns(
            "raw_material_bales",
            {
                "id": (UUID, None),
                "raw_material_batch_id": (UUID, None),
                "bale_number": (VARCHAR, 10),
                "material_type": (VARCHAR, 20),
                "dtex": (Numeric, None),
                "gross_weight_kg": (Numeric, None),
                "container_weight_kg": (Numeric, None),
                "status": (VARCHAR, 40),
            },
        )
        columns = self._columns("raw_material_bales")
        for name in ("dtex", "gross_weight_kg", "container_weight_kg"):
            self.assertIsNone(columns[name]["type"].precision)
            self.assertIsNone(columns[name]["type"].scale)

    def test_primary_and_unique_constraints_match_migration(self) -> None:
        inspector = inspect(self.engine)
        self.assertEqual(
            inspector.get_pk_constraint(
                "raw_material_batches", schema="public"
            ),
            {
                "name": "pk_raw_material_batches",
                "constrained_columns": ["id"],
                "comment": None,
                "dialect_options": {"postgresql_include": []},
            },
        )
        self.assertEqual(
            inspector.get_pk_constraint("raw_material_bales", schema="public"),
            {
                "name": "pk_raw_material_bales",
                "constrained_columns": ["id"],
                "comment": None,
                "dialect_options": {"postgresql_include": []},
            },
        )
        uniques = {
            constraint["name"]: constraint["column_names"]
            for table in TABLES
            for constraint in inspector.get_unique_constraints(
                table, schema="public"
            )
        }
        self.assertEqual(
            uniques,
            {
                "uq_raw_material_batches_shipment_number": [
                    "shipment_number"
                ],
                "uq_raw_material_bales_raw_material_batch_bale_number": [
                    "raw_material_batch_id",
                    "bale_number",
                ],
            },
        )

    def test_foreign_key_and_index_match_migration(self) -> None:
        inspector = inspect(self.engine)
        foreign_keys = inspector.get_foreign_keys(
            "raw_material_bales", schema="public"
        )
        self.assertEqual(len(foreign_keys), 1)
        foreign_key = foreign_keys[0]
        self.assertEqual(foreign_key["name"], "fk_raw_material_bales_raw_material_batch_id")
        self.assertEqual(foreign_key["constrained_columns"], ["raw_material_batch_id"])
        self.assertEqual(foreign_key["referred_schema"], "public")
        self.assertEqual(foreign_key["referred_table"], "raw_material_batches")
        self.assertEqual(foreign_key["referred_columns"], ["id"])
        self.assertEqual(foreign_key["options"].get("ondelete"), "RESTRICT")

        indexes = {
            index["name"]: index
            for index in inspector.get_indexes(
                "raw_material_bales", schema="public"
            )
            if not index.get("unique")
        }
        self.assertEqual(
            indexes["ix_raw_material_bales_raw_material_batch_id"]["column_names"],
            ["raw_material_batch_id"],
        )

    def test_status_check_accepts_lifecycle_values_and_rejects_others(self) -> None:
        batch_id = uuid4()
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "insert into public.raw_material_batches "
                    "(id, received_at, shipment_number, provider_name) "
                    "values (:id, now(), 'SHIP-STAT', 'Status provider')"
                ),
                {"id": batch_id},
            )
            for status in ("in_warehouse", "delivered"):
                connection.execute(
                    text(
                        "insert into public.raw_material_bales "
                        "(id, raw_material_batch_id, bale_number, material_type, dtex, "
                        "gross_weight_kg, container_weight_kg, status) "
                        "values (:id, :batch_id, :bale_number, 'COTTON', 2.2, 100, 5, :status)"
                    ),
                    {
                        "id": uuid4(),
                        "batch_id": batch_id,
                        "bale_number": f"BAL-{status[:3]}",
                        "status": status,
                    },
                )
        for status in ("in_production", "arbitrary"):
            with self.assertRaises(IntegrityError) as raised:
                with self.engine.begin() as connection:
                    connection.execute(
                        text(
                            "insert into public.raw_material_bales "
                            "(id, raw_material_batch_id, bale_number, material_type, dtex, "
                            "gross_weight_kg, container_weight_kg, status) "
                            "values (:id, :batch_id, :bale_number, 'COTTON', 2.2, 100, 5, :status)"
                        ),
                        {"id": uuid4(), "batch_id": batch_id, "bale_number": f"BAD-{status[:3]}", "status": status},
                    )
            self.assertEqual(
                raised.exception.orig.diag.constraint_name,
                "ck_raw_material_bales_status",
            )

    def test_rls_is_enabled_without_policies(self) -> None:
        with self.engine.connect() as connection:
            rls = connection.execute(
                text(
                    """
                    select c.relname, c.relrowsecurity
                    from pg_catalog.pg_class as c
                    join pg_catalog.pg_namespace as n on n.oid = c.relnamespace
                    where n.nspname = 'public'
                      and c.relname in (
                          'raw_material_batches', 'raw_material_bales'
                      )
                    """
                ),
            ).all()
            policies = connection.execute(
                text(
                    """
                    select tablename, policyname
                    from pg_catalog.pg_policies
                    where schemaname = 'public'
                      and tablename in (
                          'raw_material_batches', 'raw_material_bales'
                      )
                    """
                ),
            ).all()

        self.assertEqual(dict(rls), {table: True for table in TABLES})
        self.assertEqual(policies, [])

    def test_api_roles_have_no_direct_table_privileges(self) -> None:
        with self.engine.connect() as connection:
            grants = connection.execute(
                text(
                    """
                    select c.relname, grantee.rolname, acl.privilege_type
                    from pg_catalog.pg_class as c
                    join pg_catalog.pg_namespace as n on n.oid = c.relnamespace
                    cross join lateral pg_catalog.aclexplode(c.relacl) as acl
                    join pg_catalog.pg_roles as grantee
                        on grantee.oid = acl.grantee
                    where n.nspname = 'public'
                      and c.relname in (
                          'raw_material_batches', 'raw_material_bales'
                      )
                      and grantee.rolname in (
                          'anon', 'authenticated', 'service_role'
                      )
                    order by c.relname, grantee.rolname, acl.privilege_type
                    """
                ),
            ).all()

        self.assertEqual(grants, [])

    def _columns(self, table: str) -> dict[str, dict]:
        return {
            column["name"]: column
            for column in inspect(self.engine).get_columns(table, schema="public")
        }

    def _assert_columns(
        self,
        table: str,
        expected: dict[str, tuple[type, int | None]],
    ) -> None:
        columns = self._columns(table)
        self.assertEqual(set(columns), set(expected))
        for name, (expected_type, expected_length) in expected.items():
            self.assertIsInstance(columns[name]["type"], expected_type)
            self.assertFalse(columns[name]["nullable"])
            if expected_length is not None:
                self.assertEqual(columns[name]["type"].length, expected_length)


if __name__ == "__main__":
    unittest.main()
