"""Integration tests for the access control schema against real PostgreSQL.

Validates: named constraints, partial unique indexes, immutability triggers,
RLS/privilege revocations, scope-definition seed, and append-only audit behavior.

Requires: TEST_DATABASE_URL and a freshly-reset local Supabase instance
with access_control_administration migrations applied.
"""

import unittest
from uuid import uuid4

from access.application.commands import (
    ActivateRoleCommand,
    ActivateScopeCommand,
    ChangeRolePresetStatusCommand,
    CreateRoleCommand,
    CreateRolePresetCommand,
    DeactivateRoleCommand,
    DeactivateScopeCommand,
    PermissionInput,
    UpdateRoleCommand,
    UpdateRolePresetCommand,
)
from bootstrap.access_admin_dependency import admin_use_case_dependency
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.integration_tests.database_test_support import (
    test_engine,
    validated_test_database_url,
)


def _uuid() -> str:
    return str(uuid4())


def _create_operational_administrators(connection, count: int) -> None:
    system_administrator_role_id = connection.execute(
        text("SELECT role_id FROM access_roles WHERE is_system_administrator = true")
    ).scalar_one()

    for index in range(count):
        identity_subject = _uuid()
        user_id = _uuid()
        connection.execute(
            text(
                "INSERT INTO authentication_accounts "
                "(authentication_account_id, identity_subject, normalized_email, "
                "display_name, user_code, status) "
                "VALUES (:account_id, :identity_subject, :email, :display_name, "
                ":user_code, 'active')"
            ),
            {
                "account_id": _uuid(),
                "identity_subject": identity_subject,
                "email": f"continuity-{identity_subject}@example.test",
                "display_name": f"Continuity administrator {index}",
                "user_code": f"CONT-{identity_subject[:8]}",
            },
        )
        connection.execute(
            text(
                "INSERT INTO access_users "
                "(user_id, identity_subject, user_code, display_name) "
                "VALUES (:user_id, :identity_subject, :user_code, :display_name)"
            ),
            {
                "user_id": user_id,
                "identity_subject": identity_subject,
                "user_code": f"CONT-{identity_subject[:8]}",
                "display_name": f"Continuity administrator {index}",
            },
        )
        connection.execute(
            text(
                "INSERT INTO access_user_role_assignments "
                "(assignment_id, user_id, role_id, assigned_by_user_id) "
                "VALUES (:assignment_id, :user_id, :role_id, :user_id)"
            ),
            {
                "assignment_id": _uuid(),
                "user_id": user_id,
                "role_id": system_administrator_role_id,
            },
        )


class AccessSchemaConstraintsTest(unittest.TestCase):
    """Verify named constraints and partial unique indexes."""

    @classmethod
    def setUpClass(cls):
        validated_test_database_url()
        cls.engine = test_engine()

    def test_continuity_enablement_refuses_one_operational_administrator(self):
        with self.engine.connect() as connection:
            transaction = connection.begin()
            try:
                _create_operational_administrators(connection, 1)
                with self.assertRaises(Exception) as ctx:
                    with connection.begin_nested():
                        connection.execute(
                            text(
                                "UPDATE access_administrator_continuity "
                                "SET enforcement_enabled = true, "
                                "enforcement_evidence = 'migration test' "
                                "WHERE id = 1"
                            )
                        )
                self.assertIn("two operational", str(ctx.exception).lower())
                state = connection.execute(
                    text(
                        "SELECT enforcement_enabled, enforcement_enabled_at, "
                        "enforcement_evidence "
                        "FROM access_administrator_continuity WHERE id = 1"
                    )
                ).one()
                self.assertEqual(state, (False, None, None))
            finally:
                transaction.rollback()

    def test_continuity_enablement_allows_two_operational_administrators(self):
        with self.engine.connect() as connection:
            transaction = connection.begin()
            try:
                _create_operational_administrators(connection, 2)
                connection.execute(
                    text(
                        "UPDATE access_administrator_continuity "
                        "SET enforcement_enabled = true, "
                        "enforcement_evidence = 'migration test' "
                        "WHERE id = 1"
                    )
                )
                state = connection.execute(
                    text(
                        "SELECT enforcement_enabled, enforcement_enabled_at, "
                        "enforcement_evidence "
                        "FROM access_administrator_continuity WHERE id = 1"
                    )
                ).one()
                self.assertEqual(state[0], True)
                self.assertIsNotNone(state[1])
                self.assertEqual(state[2], "migration test")
            finally:
                transaction.rollback()

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
            conn.execute(
                text(
                    "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                    "VALUES (:id, 'dup-subject', 'USR-A', 'A')"
                ),
                {"id": uid1},
            )
            with self.assertRaises(Exception) as ctx:
                conn.execute(
                    text(
                        "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                        "VALUES (:id, 'dup-subject', 'USR-B', 'B')"
                    ),
                    {"id": uid2},
                )
            self.assertIn("uq_access_users_identity_subject", str(ctx.exception))
            conn.rollback()

    def test_user_identity_immutable_trigger(self):
        uid = _uuid()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                    "VALUES (:id, 'immutable-test', 'USR-IMM', 'Immutable')"
                ),
                {"id": uid},
            )
            with self.assertRaises(Exception) as ctx:
                conn.execute(
                    text(
                        "UPDATE access_users SET identity_subject = 'changed' WHERE user_id = :id"
                    ),
                    {"id": uid},
                )
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
                conn.execute(
                    text(
                        "INSERT INTO access_roles (role_id, role_code, role_name, is_system_administrator) "
                        "VALUES (:id, 'sysadmin2', 'Another Admin', true)"
                    ),
                    {"id": r2},
                )
            self.assertIn("uq_access_roles_single_sysadmin", str(ctx.exception))
            conn.rollback()

    def test_current_assignment_partial_unique(self):
        uid = _uuid()
        rid = _uuid()
        a1 = _uuid()
        a2 = _uuid()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                    "VALUES (:id, 'assign-test', 'USR-AT', 'Assign')"
                ),
                {"id": uid},
            )
            conn.execute(
                text(
                    "INSERT INTO access_roles (role_id, role_code, role_name) "
                    "VALUES (:id, 'test-role', 'Test Role')"
                ),
                {"id": rid},
            )
            conn.execute(
                text(
                    "INSERT INTO access_user_role_assignments "
                    "(assignment_id, user_id, role_id, assigned_by_user_id) "
                    "VALUES (:aid, :uid, :rid, :uid)"
                ),
                {"aid": a1, "uid": uid, "rid": rid},
            )
            # Second current assignment for same user+role should fail
            with self.assertRaises(Exception) as ctx:
                conn.execute(
                    text(
                        "INSERT INTO access_user_role_assignments "
                        "(assignment_id, user_id, role_id, assigned_by_user_id) "
                        "VALUES (:aid, :uid, :rid, :uid)"
                    ),
                    {"aid": a2, "uid": uid, "rid": rid},
                )
            self.assertIn("uq_access_assignments_current", str(ctx.exception))
            conn.rollback()

    def test_revoked_assignment_allows_new_current(self):
        uid = _uuid()
        rid = _uuid()
        a1 = _uuid()
        a2 = _uuid()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                    "VALUES (:id, 'revoke-test', 'USR-RT', 'Revoke')"
                ),
                {"id": uid},
            )
            conn.execute(
                text(
                    "INSERT INTO access_roles (role_id, role_code, role_name) "
                    "VALUES (:id, 'revoke-role', 'Revoke Role')"
                ),
                {"id": rid},
            )
            # First assignment, then revoke it
            conn.execute(
                text(
                    "INSERT INTO access_user_role_assignments "
                    "(assignment_id, user_id, role_id, assigned_by_user_id, "
                    "revoked_at, revoked_by_user_id, revoke_reason) "
                    "VALUES (:aid, :uid, :rid, :uid, now(), :uid, 'test')"
                ),
                {"aid": a1, "uid": uid, "rid": rid},
            )
            # New current assignment should succeed (old is revoked)
            conn.execute(
                text(
                    "INSERT INTO access_user_role_assignments "
                    "(assignment_id, user_id, role_id, assigned_by_user_id) "
                    "VALUES (:aid, :uid, :rid, :uid)"
                ),
                {"aid": a2, "uid": uid, "rid": rid},
            )
            conn.rollback()

    def test_audit_append_only_trigger(self):
        uid = _uuid()
        audit_id = _uuid()
        op_id = _uuid()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                    "VALUES (:id, 'audit-test', 'USR-AUD', 'Audit')"
                ),
                {"id": uid},
            )
            conn.execute(
                text(
                    "INSERT INTO access_change_audits "
                    "(access_change_audit_id, operation_id, change_kind, "
                    "subject_type, subject_id, performed_by_user_id, reason) "
                    "VALUES (:aid, :oid, 'role_created', 'role', :sid, :uid, 'test')"
                ),
                {"aid": audit_id, "oid": op_id, "sid": _uuid(), "uid": uid},
            )
            with self.assertRaises(Exception) as ctx:
                conn.execute(
                    text(
                        "UPDATE access_change_audits SET reason = 'hacked' "
                        "WHERE access_change_audit_id = :id"
                    ),
                    {"id": audit_id},
                )
            self.assertIn("append-only", str(ctx.exception).lower())
            conn.rollback()

    def test_scope_references_definition_key_fk(self):
        sid = _uuid()
        with self.engine.begin() as conn:
            # Valid: references existing definition
            conn.execute(
                text(
                    "INSERT INTO access_scopes "
                    "(scope_id, definition_key, scope_code, scope_name, owning_context, description) "
                    "VALUES (:id, 'warehouse.raw_materials', :code, 'Raw Materials', 'Warehouse', 'Admin')"
                ),
                {"id": sid, "code": f"warehouse-test-{sid[:8]}"},
            )
            conn.rollback()

    def test_scope_rejects_unknown_definition_key(self):
        sid = _uuid()
        with self.engine.begin() as conn:
            with self.assertRaises(Exception) as ctx:
                conn.execute(
                    text(
                        "INSERT INTO access_scopes "
                        "(scope_id, definition_key, scope_code, scope_name, owning_context, description) "
                        "VALUES (:id, 'unknown.scope', 'unknown.scope', 'X', 'X', 'X')"
                    ),
                    {"id": sid},
                )
            self.assertIn("fk_access_scopes_definition", str(ctx.exception))
            conn.rollback()

    def test_role_preset_code_and_permission_triples_are_unique(self):
        preset_id, user_id, scope_id = _uuid(), _uuid(), _uuid()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) VALUES (:id, :subject, :code, 'Preset actor')"
                ),
                {
                    "id": user_id,
                    "subject": f"preset-{user_id}",
                    "code": f"USR-{user_id[:6]}",
                },
            )
            conn.execute(
                text(
                    "INSERT INTO access_scopes (scope_id, definition_key, scope_code, scope_name, owning_context, description) VALUES (:id, 'warehouse.raw_materials', :code, 'Access', 'Access', 'test')"
                ),
                {"id": scope_id, "code": f"access-preset-{scope_id[:8]}"},
            )
            conn.execute(
                text(
                    "INSERT INTO access_role_presets (preset_id, preset_code, preset_name) VALUES (:id, 'preset-unique', 'Preset')"
                ),
                {"id": preset_id},
            )
            conn.execute(
                text(
                    "INSERT INTO access_role_preset_permissions (preset_id, scope_id, action, created_by_user_id) VALUES (:preset, :scope, 'read', :user)"
                ),
                {"preset": preset_id, "scope": scope_id, "user": user_id},
            )
            with self.assertRaises(Exception) as ctx:
                conn.execute(
                    text(
                        "INSERT INTO access_role_preset_permissions (preset_id, scope_id, action, created_by_user_id) VALUES (:preset, :scope, 'read', :user)"
                    ),
                    {"preset": preset_id, "scope": scope_id, "user": user_id},
                )
            self.assertIn(
                "uq_access_role_preset_permissions_triple", str(ctx.exception)
            )
            conn.rollback()

    def test_preset_creation_rejects_inactive_scope(self):
        from access.adapters.persistence.audit_repository import (
            AccessAuditRepositoryAdapter,
        )
        from access.adapters.persistence.preset_repository import (
            RolePresetRepositoryAdapter,
        )
        from access.adapters.persistence.scope_repository import (
            ScopeDefinitionRegistryAdapter,
            ScopeRepositoryAdapter,
        )
        from access.adapters.persistence.transaction import TransactionAdapter
        from access.application.commands import CreateRolePresetCommand, PermissionInput
        from access.application.create_role_preset import CreateRolePreset
        from access.domain.errors import InactiveAccessScope
        from infra.clock import SystemClock
        from infra.identity import SystemIdentity

        actor_id, scope_id = _uuid(), _uuid()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) VALUES (:id, :subject, :code, 'Actor')"
                ),
                {
                    "id": actor_id,
                    "subject": f"inactive-{actor_id}",
                    "code": f"USR-{actor_id[:6]}",
                },
            )
            conn.execute(
                text(
                    "INSERT INTO access_scopes (scope_id, definition_key, scope_code, scope_name, owning_context, description, is_active) VALUES (:id, 'warehouse.raw_materials', :code, 'Raw', 'Warehouse', 'test', false)"
                ),
                {"id": scope_id, "code": f"warehouse-inactive-{scope_id[:8]}"},
            )
        session = Session(self.engine)
        try:
            use_case = CreateRolePreset(
                preset_repository=RolePresetRepositoryAdapter(session),
                scope_repository=ScopeRepositoryAdapter(session),
                scope_definition_registry=ScopeDefinitionRegistryAdapter(session),
                audit_repository=AccessAuditRepositoryAdapter(session),
                transaction=TransactionAdapter(session),
                clock=SystemClock(),
                identity=SystemIdentity(),
            )
            with self.assertRaises(InactiveAccessScope):
                use_case.execute(
                    CreateRolePresetCommand(
                        "inactive-scope-preset",
                        "Inactive",
                        None,
                        [PermissionInput("read", scope_id)],
                        "test",
                        actor_id,
                        _uuid(),
                    )
                )
        finally:
            session.rollback()
            session.close()
            with self.engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM access_scopes WHERE scope_id = :id"),
                    {"id": scope_id},
                )
                conn.execute(
                    text("DELETE FROM access_users WHERE user_id = :id"),
                    {"id": actor_id},
                )

    def test_role_preset_and_scope_lifecycles_are_audited_and_rolled_back(self):
        actor_id = _uuid()
        scope_id = _uuid()
        evidence_tag = uuid4().hex
        operation_ids = {
            name: _uuid()
            for name in (
                "scope_deactivated",
                "scope_activated",
                "role_created",
                "role_updated",
                "role_deactivated",
                "role_activated",
                "role_preset_created",
                "role_preset_updated",
                "role_preset_deactivated",
                "role_preset_activated",
            )
        }
        connection = self.engine.connect()
        outer_transaction = connection.begin()
        session = Session(bind=connection)
        try:
            session.execute(
                text(
                    "INSERT INTO access_users "
                    "(user_id, identity_subject, user_code, display_name) "
                    "VALUES (:id, :subject, :code, 'Lifecycle evidence actor')"
                ),
                {
                    "id": actor_id,
                    "subject": f"lifecycle-evidence-{evidence_tag}",
                    "code": f"EVID-{evidence_tag[:12]}",
                },
            )
            session.execute(
                text(
                    "INSERT INTO access_scopes "
                    "(scope_id, definition_key, scope_code, scope_name, owning_context, description) "
                    "VALUES (:id, 'warehouse.raw_materials', :code, "
                    "'Lifecycle evidence scope', 'Warehouse', 'test fixture')"
                ),
                {"id": scope_id, "code": f"lifecycle-scope-{evidence_tag}"},
            )
            scope_id = session.execute(
                text(
                    "SELECT s.scope_id FROM access_scopes s "
                    "JOIN access_scope_definitions d "
                    "ON d.definition_key = s.definition_key "
                    "WHERE s.is_active AND 'read' = ANY(d.supported_actions) "
                    "ORDER BY s.scope_code LIMIT 1"
                )
            ).scalar_one()

            def session_provider():
                yield session

            use_cases = admin_use_case_dependency(session_provider)(session)
            scope = use_cases.scope_repository.find_by_id(str(scope_id))
            assert scope is not None
            use_cases.deactivate_scope.execute(
                DeactivateScopeCommand(
                    scope.scope_id,
                    scope.version,
                    "Issue 83 lifecycle evidence",
                    actor_id,
                    operation_ids["scope_deactivated"],
                )
            )
            use_cases.activate_scope.execute(
                ActivateScopeCommand(
                    scope.scope_id,
                    scope.version + 1,
                    "Issue 83 lifecycle evidence",
                    actor_id,
                    operation_ids["scope_activated"],
                )
            )

            role = use_cases.create_role.execute(
                CreateRoleCommand(
                    f"evidence-role-{evidence_tag}",
                    "Lifecycle evidence role",
                    None,
                    [PermissionInput("read", scope.scope_id)],
                    "Issue 83 lifecycle evidence",
                    actor_id,
                    operation_ids["role_created"],
                )
            )
            role = use_cases.update_role.execute(
                UpdateRoleCommand(
                    role.role_id,
                    "Updated lifecycle evidence role",
                    None,
                    [PermissionInput("read", scope.scope_id)],
                    role.version,
                    "Issue 83 lifecycle evidence",
                    actor_id,
                    operation_ids["role_updated"],
                )
            )
            use_cases.deactivate_role.execute(
                DeactivateRoleCommand(
                    role.role_id,
                    role.version,
                    "Issue 83 lifecycle evidence",
                    actor_id,
                    operation_ids["role_deactivated"],
                )
            )
            use_cases.activate_role.execute(
                ActivateRoleCommand(
                    role.role_id,
                    role.version + 1,
                    "Issue 83 lifecycle evidence",
                    actor_id,
                    operation_ids["role_activated"],
                )
            )

            preset = use_cases.create_role_preset.execute(
                CreateRolePresetCommand(
                    f"evidence-preset-{evidence_tag}",
                    "Lifecycle evidence preset",
                    None,
                    [PermissionInput("read", scope.scope_id)],
                    "Issue 83 lifecycle evidence",
                    actor_id,
                    operation_ids["role_preset_created"],
                )
            )
            preset = use_cases.update_role_preset.execute(
                UpdateRolePresetCommand(
                    preset.preset_id,
                    "Updated lifecycle evidence preset",
                    None,
                    [PermissionInput("read", scope.scope_id)],
                    preset.version,
                    "Issue 83 lifecycle evidence",
                    actor_id,
                    operation_ids["role_preset_updated"],
                )
            )
            use_cases.change_role_preset_status.execute(
                ChangeRolePresetStatusCommand(
                    preset.preset_id,
                    False,
                    preset.version,
                    "Issue 83 lifecycle evidence",
                    actor_id,
                    operation_ids["role_preset_deactivated"],
                )
            )
            use_cases.change_role_preset_status.execute(
                ChangeRolePresetStatusCommand(
                    preset.preset_id,
                    True,
                    preset.version + 1,
                    "Issue 83 lifecycle evidence",
                    actor_id,
                    operation_ids["role_preset_activated"],
                )
            )

            audit_rows = (
                session.execute(
                    text(
                        "SELECT change_kind, subject_type, before_values, after_values "
                        "FROM access_change_audits "
                        "WHERE operation_id = ANY(CAST(:operation_ids AS uuid[]))"
                    ),
                    {"operation_ids": list(operation_ids.values())},
                )
                .mappings()
                .all()
            )
            self.assertEqual(
                {(row["change_kind"], row["subject_type"]) for row in audit_rows},
                {
                    (
                        name,
                        (
                            "role_preset"
                            if name.startswith("role_preset_")
                            else name.split("_", 1)[0]
                        ),
                    )
                    for name in operation_ids
                },
            )
            self.assertTrue(
                all(
                    row["before_values"] is not None and row["after_values"] is not None
                    for row in audit_rows
                )
            )
        finally:
            if outer_transaction.is_active:
                outer_transaction.rollback()
            session.close()
            connection.close()

        with self.engine.connect() as verification_connection:
            remaining = verification_connection.execute(
                text(
                    "SELECT "
                    "(SELECT count(*) FROM access_change_audits "
                    " WHERE operation_id = ANY(CAST(:operation_ids AS uuid[]))), "
                    "(SELECT count(*) FROM access_users WHERE user_id = :actor_id), "
                    "(SELECT count(*) FROM access_roles WHERE role_code = :role_code), "
                    "(SELECT count(*) FROM access_role_presets WHERE preset_code = :preset_code)"
                ),
                {
                    "operation_ids": list(operation_ids.values()),
                    "actor_id": actor_id,
                    "role_code": f"evidence-role-{evidence_tag}",
                    "preset_code": f"evidence-preset-{evidence_tag}",
                },
            ).one()
            self.assertEqual(tuple(remaining), (0, 0, 0, 0))
            remaining_scope_count = verification_connection.execute(
                text("SELECT count(*) FROM access_scopes WHERE scope_id = :scope_id"),
                {"scope_id": scope_id},
            ).scalar_one()
            self.assertEqual(remaining_scope_count, 0)

    def test_audit_repository_reads_absent_and_empty_reasons(self):
        from access.adapters.persistence.audit_repository import (
            AccessAuditRepositoryAdapter,
        )

        actor_id, subject_id = _uuid(), _uuid()
        absent_operation_id, empty_operation_id = _uuid(), _uuid()

        connection = self.engine.connect()
        outer_transaction = connection.begin()
        session = Session(bind=connection)

        try:
            session.execute(
                text(
                    "INSERT INTO access_users "
                    "(user_id, identity_subject, user_code, display_name) "
                    "VALUES (:id, :subject, :code, 'Audit actor')"
                ),
                {
                    "id": actor_id,
                    "subject": f"audit-actor-{actor_id}",
                    "code": f"AUD-{actor_id[:8]}",
                },
            )

            repository = AccessAuditRepositoryAdapter(session)

            for operation_id, reason in (
                (absent_operation_id, None),
                (empty_operation_id, ""),
            ):
                repository.append(
                    operation_id=operation_id,
                    change_kind="role_updated",
                    subject_type="role",
                    subject_id=subject_id,
                    performed_by_user_id=actor_id,
                    reason=reason,
                    before_values={},
                    after_values={},
                )

            session.flush()

            entries = {
                entry.operation_id: entry for entry in repository.list_recent(limit=10)
            }

            self.assertIsNone(entries[absent_operation_id].reason)
            self.assertEqual(entries[empty_operation_id].reason, "")

        finally:
            if outer_transaction.is_active:
                outer_transaction.rollback()
            session.close()
            connection.close()


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
                    result = conn.execute(
                        text(
                            "SELECT relrowsecurity FROM pg_class WHERE relname = :name"
                        ),
                        {"name": table},
                    ).scalar()
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
                        result = conn.execute(
                            text("SELECT has_table_privilege(:role, :table, 'SELECT')"),
                            {"role": role, "table": f"public.{table}"},
                        ).scalar()
                        self.assertFalse(
                            result,
                            f"{role} has SELECT on {table}",
                        )


if __name__ == "__main__":
    unittest.main()
