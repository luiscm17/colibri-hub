"""Integration tests for the access control schema against real PostgreSQL.

Validates: named constraints, partial unique indexes, immutability triggers,
RLS/privilege revocations, scope-definition seed, and append-only audit behavior.

Requires: TEST_DATABASE_URL and a freshly-reset local Supabase instance
with access_control_administration migrations applied.
"""

import unittest
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.integration_tests.database_test_support import (
    test_engine,
    validated_test_database_url,
)


def _uuid() -> str:
    return str(uuid4())


class AccessSchemaConstraintsTest(unittest.TestCase):
    """Verify named constraints and partial unique indexes."""

    @classmethod
    def setUpClass(cls):
        validated_test_database_url()
        cls.engine = test_engine()

    def test_scope_definitions_seeded_with_19_rows(self):
        with self.engine.connect() as conn:
            count = conn.execute(
                text("SELECT count(*) FROM access_scope_definitions")
            ).scalar()
        self.assertEqual(count, 19)

    def test_scope_definitions_immutable_trigger(self):
        with self.engine.begin() as conn:
            with self.assertRaises(Exception) as ctx:
                conn.execute(
                    text(
                        "UPDATE access_scope_definitions "
                        "SET scope_name = 'Hacked' "
                        "WHERE definition_key = 'access_control'"
                    )
                )
            self.assertIn("immutable", str(ctx.exception).lower())

    def test_scope_definitions_delete_blocked(self):
        with self.engine.begin() as conn:
            with self.assertRaises(Exception) as ctx:
                conn.execute(
                    text(
                        "DELETE FROM access_scope_definitions "
                        "WHERE definition_key = 'access_control'"
                    )
                )
            self.assertIn("immutable", str(ctx.exception).lower())

    def test_user_identity_subject_unique(self):
        uid1 = _uuid()
        uid2 = _uuid()
        with self.engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                "VALUES (:id, 'dup-subject', 'USR-A', 'A')"
            ), {"id": uid1})
            with self.assertRaises(Exception) as ctx:
                conn.execute(text(
                    "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                    "VALUES (:id, 'dup-subject', 'USR-B', 'B')"
                ), {"id": uid2})
            self.assertIn("uq_access_users_identity_subject", str(ctx.exception))
            conn.rollback()

    def test_user_identity_immutable_trigger(self):
        uid = _uuid()
        with self.engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                "VALUES (:id, 'immutable-test', 'USR-IMM', 'Immutable')"
            ), {"id": uid})
            with self.assertRaises(Exception) as ctx:
                conn.execute(text(
                    "UPDATE access_users SET identity_subject = 'changed' WHERE user_id = :id"
                ), {"id": uid})
            self.assertIn("immutable", str(ctx.exception).lower())
            conn.rollback()

    def test_single_system_administrator_role_constraint(self):
        # The system_administrator role is seeded by migration
        # 20260806120000_seed_system_administrator_role.sql.
        # Inserting a second is_system_administrator=true role must fail the
        # partial unique index uq_access_roles_single_sysadmin.
        r2 = _uuid()
        with self.engine.begin() as conn:
            with self.assertRaises(Exception) as ctx:
                conn.execute(text(
                    "INSERT INTO access_roles (role_id, role_code, role_name, is_system_administrator) "
                    "VALUES (:id, 'sysadmin2', 'Another Admin', true)"
                ), {"id": r2})
            self.assertIn("uq_access_roles_single_sysadmin", str(ctx.exception))
            conn.rollback()

    def test_current_assignment_partial_unique(self):
        uid = _uuid()
        rid = _uuid()
        a1 = _uuid()
        a2 = _uuid()
        with self.engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                "VALUES (:id, 'assign-test', 'USR-AT', 'Assign')"
            ), {"id": uid})
            conn.execute(text(
                "INSERT INTO access_roles (role_id, role_code, role_name) "
                "VALUES (:id, 'test-role', 'Test Role')"
            ), {"id": rid})
            conn.execute(text(
                "INSERT INTO access_user_role_assignments "
                "(assignment_id, user_id, role_id, assigned_by_user_id) "
                "VALUES (:aid, :uid, :rid, :uid)"
            ), {"aid": a1, "uid": uid, "rid": rid})
            # Second current assignment for same user+role should fail
            with self.assertRaises(Exception) as ctx:
                conn.execute(text(
                    "INSERT INTO access_user_role_assignments "
                    "(assignment_id, user_id, role_id, assigned_by_user_id) "
                    "VALUES (:aid, :uid, :rid, :uid)"
                ), {"aid": a2, "uid": uid, "rid": rid})
            self.assertIn("uq_access_assignments_current", str(ctx.exception))
            conn.rollback()

    def test_revoked_assignment_allows_new_current(self):
        uid = _uuid()
        rid = _uuid()
        a1 = _uuid()
        a2 = _uuid()
        with self.engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                "VALUES (:id, 'revoke-test', 'USR-RT', 'Revoke')"
            ), {"id": uid})
            conn.execute(text(
                "INSERT INTO access_roles (role_id, role_code, role_name) "
                "VALUES (:id, 'revoke-role', 'Revoke Role')"
            ), {"id": rid})
            # First assignment, then revoke it
            conn.execute(text(
                "INSERT INTO access_user_role_assignments "
                "(assignment_id, user_id, role_id, assigned_by_user_id, "
                "revoked_at, revoked_by_user_id, revoke_reason) "
                "VALUES (:aid, :uid, :rid, :uid, now(), :uid, 'test')"
            ), {"aid": a1, "uid": uid, "rid": rid})
            # New current assignment should succeed (old is revoked)
            conn.execute(text(
                "INSERT INTO access_user_role_assignments "
                "(assignment_id, user_id, role_id, assigned_by_user_id) "
                "VALUES (:aid, :uid, :rid, :uid)"
            ), {"aid": a2, "uid": uid, "rid": rid})
            conn.rollback()

    def test_audit_append_only_trigger(self):
        uid = _uuid()
        audit_id = _uuid()
        op_id = _uuid()
        with self.engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                "VALUES (:id, 'audit-test', 'USR-AUD', 'Audit')"
            ), {"id": uid})
            conn.execute(text(
                "INSERT INTO access_change_audits "
                "(access_change_audit_id, operation_id, change_kind, "
                "subject_type, subject_id, performed_by_user_id, reason) "
                "VALUES (:aid, :oid, 'role_created', 'role', :sid, :uid, 'test')"
            ), {"aid": audit_id, "oid": op_id, "sid": _uuid(), "uid": uid})
            with self.assertRaises(Exception) as ctx:
                conn.execute(text(
                    "UPDATE access_change_audits SET reason = 'hacked' "
                    "WHERE access_change_audit_id = :id"
                ), {"id": audit_id})
            self.assertIn("append-only", str(ctx.exception).lower())
            conn.rollback()

    def test_scope_references_definition_key_fk(self):
        sid = _uuid()
        with self.engine.begin() as conn:
            # Valid: references existing definition
            conn.execute(text(
                "INSERT INTO access_scopes "
                "(scope_id, definition_key, scope_code, scope_name, owning_context, description) "
                "VALUES (:id, 'warehouse.raw_materials', :code, 'Raw Materials', 'Warehouse', 'Admin')"
            ), {"id": sid, "code": f"warehouse-test-{sid[:8]}"})
            conn.rollback()

    def test_scope_rejects_unknown_definition_key(self):
        sid = _uuid()
        with self.engine.begin() as conn:
            with self.assertRaises(Exception) as ctx:
                conn.execute(text(
                    "INSERT INTO access_scopes "
                    "(scope_id, definition_key, scope_code, scope_name, owning_context, description) "
                    "VALUES (:id, 'unknown.scope', 'unknown.scope', 'X', 'X', 'X')"
                ), {"id": sid})
            self.assertIn("fk_access_scopes_definition", str(ctx.exception))
            conn.rollback()

    def test_role_preset_code_and_permission_triples_are_unique(self):
        preset_id, user_id, scope_id = _uuid(), _uuid(), _uuid()
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO access_users (user_id, identity_subject, user_code, display_name) VALUES (:id, :subject, :code, 'Preset actor')"), {"id": user_id, "subject": f"preset-{user_id}", "code": f"USR-{user_id[:6]}"})
            conn.execute(text("INSERT INTO access_scopes (scope_id, definition_key, scope_code, scope_name, owning_context, description) VALUES (:id, 'warehouse.raw_materials', :code, 'Access', 'Access', 'test')"), {"id": scope_id, "code": f"access-preset-{scope_id[:8]}"})
            conn.execute(text("INSERT INTO access_role_presets (preset_id, preset_code, preset_name) VALUES (:id, 'preset-unique', 'Preset')"), {"id": preset_id})
            conn.execute(text("INSERT INTO access_role_preset_permissions (preset_id, scope_id, action, created_by_user_id) VALUES (:preset, :scope, 'read', :user)"), {"preset": preset_id, "scope": scope_id, "user": user_id})
            with self.assertRaises(Exception) as ctx:
                conn.execute(text("INSERT INTO access_role_preset_permissions (preset_id, scope_id, action, created_by_user_id) VALUES (:preset, :scope, 'read', :user)"), {"preset": preset_id, "scope": scope_id, "user": user_id})
            self.assertIn("uq_access_role_preset_permissions_triple", str(ctx.exception))
            conn.rollback()

    def test_preset_creation_rejects_inactive_scope(self):
        from access.adapters.persistence.audit_repository import AccessAuditRepositoryAdapter
        from access.adapters.persistence.preset_repository import RolePresetRepositoryAdapter
        from access.adapters.persistence.scope_repository import ScopeDefinitionRegistryAdapter, ScopeRepositoryAdapter
        from access.adapters.persistence.transaction import TransactionAdapter
        from access.application.commands import CreateRolePresetCommand, PermissionInput
        from access.application.create_role_preset import CreateRolePreset
        from access.domain.errors import InactiveAccessScope
        from infra.clock import SystemClock
        from infra.identity import SystemIdentity

        actor_id, scope_id = _uuid(), _uuid()
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO access_users (user_id, identity_subject, user_code, display_name) VALUES (:id, :subject, :code, 'Actor')"), {"id": actor_id, "subject": f"inactive-{actor_id}", "code": f"USR-{actor_id[:6]}"})
            conn.execute(text("INSERT INTO access_scopes (scope_id, definition_key, scope_code, scope_name, owning_context, description, is_active) VALUES (:id, 'warehouse.raw_materials', :code, 'Raw', 'Warehouse', 'test', false)"), {"id": scope_id, "code": f"warehouse-inactive-{scope_id[:8]}"})
        session = Session(self.engine)
        try:
            use_case = CreateRolePreset(preset_repository=RolePresetRepositoryAdapter(session), scope_repository=ScopeRepositoryAdapter(session), scope_definition_registry=ScopeDefinitionRegistryAdapter(session), audit_repository=AccessAuditRepositoryAdapter(session), transaction=TransactionAdapter(session), clock=SystemClock(), identity=SystemIdentity())
            with self.assertRaises(InactiveAccessScope):
                use_case.execute(CreateRolePresetCommand("inactive-scope-preset", "Inactive", None, [PermissionInput("read", scope_id)], "test", actor_id, _uuid()))
        finally:
            session.rollback(); session.close()
            with self.engine.begin() as conn:
                conn.execute(text("DELETE FROM access_scopes WHERE scope_id = :id"), {"id": scope_id})
                conn.execute(text("DELETE FROM access_users WHERE user_id = :id"), {"id": actor_id})


class AccessSchemaRlsTest(unittest.TestCase):
    """Verify RLS and privilege revocations."""

    @classmethod
    def setUpClass(cls):
        validated_test_database_url()
        cls.engine = test_engine()

    def test_rls_enabled_on_all_access_tables(self):
        tables = [
            "access_scope_definitions",
            "access_users",
            "access_roles",
            "access_scopes",
            "access_role_permissions",
            "access_user_role_assignments",
            "access_change_audits",
            "access_role_presets",
            "access_role_preset_permissions",
        ]
        with self.engine.connect() as conn:
            for table in tables:
                with self.subTest(table=table):
                    result = conn.execute(text(
                        "SELECT relrowsecurity FROM pg_class "
                        "WHERE relname = :name"
                    ), {"name": table}).scalar()
                    self.assertTrue(
                        result,
                        f"RLS not enabled on {table}",
                    )

    def test_browser_roles_have_no_privileges(self):
        tables = [
            "access_scope_definitions",
            "access_users",
            "access_roles",
            "access_scopes",
            "access_role_permissions",
            "access_user_role_assignments",
            "access_change_audits",
            "access_role_presets",
            "access_role_preset_permissions",
        ]
        with self.engine.connect() as conn:
            for table in tables:
                for role in ("anon", "authenticated", "service_role"):
                    with self.subTest(table=table, role=role):
                        result = conn.execute(text(
                            "SELECT has_table_privilege(:role, :table, 'SELECT')"
                        ), {"role": role, "table": f"public.{table}"}).scalar()
                        self.assertFalse(
                            result,
                            f"{role} has SELECT on {table}",
                        )


if __name__ == "__main__":
    unittest.main()
