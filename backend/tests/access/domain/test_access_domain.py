"""Unit tests for access domain: actions, entities, value objects, and authorization.

Validates correctness properties from design §Correctness Properties 1–4.
"""

import unittest
from datetime import UTC, datetime

from access.domain.actions import PRIVILEGED_ACTIONS, Action, Permission
from access.domain.authorization import authorize, effective_permissions
from access.domain.roles import Assignment, Role
from access.domain.scopes import Scope, ScopeCode, ScopeDefinition
from access.domain.users import AccessUser

NOW = datetime(2025, 1, 1, tzinfo=UTC)


def _user(user_id="user-1", is_active=True) -> AccessUser:
    return AccessUser(
        user_id=user_id,
        identity_subject=f"sub-{user_id}",
        user_code=f"USR-{user_id}",
        display_name="Test User",
        is_active=is_active,
        authorization_version=1,
        version=1,
        created_at=NOW,
        updated_at=NOW,
    )


def _role(
    role_id="role-1",
    role_code="reader",
    is_system_administrator=False,
    is_active=True,
    permissions=None,
) -> Role:
    return Role(
        role_id=role_id,
        role_code=role_code,
        role_name="Test Role",
        description=None,
        is_system_administrator=is_system_administrator,
        is_active=is_active,
        version=1,
        permissions=permissions or set(),
    )


def _scope(scope_id="scope-1", scope_code="warehouse.raw_materials", is_active=True) -> Scope:
    return Scope(
        scope_id=scope_id,
        definition_key=scope_code,
        scope_code=scope_code,
        scope_name="Test Scope",
        owning_context="Test",
        description="Test scope",
        is_active=is_active,
        version=1,
        created_at=NOW,
        updated_at=NOW,
    )


def _assignment(user_id="user-1", role_id="role-1") -> Assignment:
    return Assignment(
        assignment_id=f"asgn-{user_id}-{role_id}",
        user_id=user_id,
        role_id=role_id,
        assigned_by_user_id="admin-1",
        assigned_at=NOW,
    )


# --- Action Enum ---


class ActionEnumTest(unittest.TestCase):
    """Verify the 5 supported action values per §6.1."""

    def test_has_exactly_five_members(self):
        self.assertEqual(len(Action), 5)

    def test_values_match_spec(self):
        expected = {"read", "write", "edit", "edit_outside_window", "manage_access"}
        self.assertEqual(set(Action), expected)

    def test_action_is_str_enum(self):
        self.assertEqual(Action.READ, "read")
        self.assertEqual(Action.MANAGE_ACCESS, "manage_access")

    def test_construct_from_string(self):
        self.assertEqual(Action("read"), Action.READ)

    def test_invalid_action_string_raises(self):
        with self.assertRaises(ValueError):
            Action("invalid")

    def test_privileged_actions_set(self):
        self.assertEqual(PRIVILEGED_ACTIONS, frozenset({Action.MANAGE_ACCESS, Action.EDIT_OUTSIDE_WINDOW}))


# --- Permission Value Object ---


class PermissionTest(unittest.TestCase):
    """Verify Permission value object behavior."""

    def test_frozen(self):
        p = Permission(action=Action.READ, scope_code="warehouse.raw_materials")
        with self.assertRaises(AttributeError):
            p.action = Action.WRITE  # type: ignore[misc]

    def test_equality_by_value(self):
        p1 = Permission(action=Action.READ, scope_code="warehouse.raw_materials")
        p2 = Permission(action=Action.READ, scope_code="warehouse.raw_materials")
        self.assertEqual(p1, p2)

    def test_hashable_for_sets(self):
        p1 = Permission(action=Action.READ, scope_code="warehouse.raw_materials")
        p2 = Permission(action=Action.READ, scope_code="warehouse.raw_materials")
        self.assertEqual(len({p1, p2}), 1)

    def test_scope_code_non_empty(self):
        with self.assertRaises(ValueError):
            Permission(action=Action.READ, scope_code="")

    def test_scope_code_trimmed(self):
        with self.assertRaises(ValueError):
            Permission(action=Action.READ, scope_code=" warehouse ")


# --- ScopeCode Value Object ---


class ScopeCodeTest(unittest.TestCase):
    def test_valid(self):
        sc = ScopeCode("warehouse.raw_materials")
        self.assertEqual(sc.value, "warehouse.raw_materials")

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            ScopeCode("")

    def test_whitespace_rejected(self):
        with self.assertRaises(ValueError):
            ScopeCode(" warehouse.raw_materials ")

    def test_frozen(self):
        sc = ScopeCode("access_control")
        with self.assertRaises(AttributeError):
            sc.value = "other"  # type: ignore[misc]

    def test_equality(self):
        self.assertEqual(ScopeCode("access_control"), ScopeCode("access_control"))
        self.assertNotEqual(ScopeCode("access_control"), ScopeCode("warehouse.raw_materials"))


# --- ScopeDefinition ---


class ScopeDefinitionTest(unittest.TestCase):
    def test_frozen(self):
        sd = ScopeDefinition(
            definition_key="access_control",
            scope_code="access_control",
            scope_name="Access Control",
            owning_context="Access Control",
            description="Administration",
            supported_actions=frozenset({Action.MANAGE_ACCESS}),
        )
        with self.assertRaises(AttributeError):
            sd.scope_code = "other"  # type: ignore[misc]

    def test_supported_actions(self):
        sd = ScopeDefinition(
            definition_key="warehouse.raw_materials",
            scope_code="warehouse.raw_materials",
            scope_name="Warehouse Raw Materials",
            owning_context="Warehouse",
            description="Raw-material operations",
            supported_actions=frozenset({Action.READ, Action.WRITE, Action.EDIT}),
        )
        self.assertIn(Action.READ, sd.supported_actions)
        self.assertNotIn(Action.MANAGE_ACCESS, sd.supported_actions)


# --- Scope Entity Behavior ---


class ScopeBehaviorTest(unittest.TestCase):
    def test_deactivate_sets_inactive_and_bumps_version(self):
        scope = _scope()
        later = datetime(2025, 6, 1, tzinfo=UTC)
        scope.deactivate(at=later)
        self.assertFalse(scope.is_active)
        self.assertEqual(scope.version, 2)
        self.assertEqual(scope.updated_at, later)

    def test_deactivate_idempotent_when_already_inactive(self):
        scope = _scope(is_active=False)
        original_version = scope.version
        scope.deactivate(at=datetime(2025, 6, 1, tzinfo=UTC))
        self.assertEqual(scope.version, original_version)

    def test_activate_sets_active_and_bumps_version(self):
        scope = _scope(is_active=False)
        later = datetime(2025, 6, 1, tzinfo=UTC)
        scope.activate(at=later)
        self.assertTrue(scope.is_active)
        self.assertEqual(scope.version, 2)
        self.assertEqual(scope.updated_at, later)

    def test_activate_idempotent_when_already_active(self):
        scope = _scope()
        original_version = scope.version
        scope.activate(at=datetime(2025, 6, 1, tzinfo=UTC))
        self.assertEqual(scope.version, original_version)


# --- AccessUser Entity ---


class AccessUserTest(unittest.TestCase):
    def test_creation(self):
        user = _user()
        self.assertTrue(user.is_active)
        self.assertEqual(user.authorization_version, 1)

    def test_deactivation(self):
        user = _user()
        user.is_active = False
        self.assertFalse(user.is_active)

    def test_version_bump(self):
        user = _user()
        user.authorization_version += 1
        self.assertEqual(user.authorization_version, 2)

    def test_deactivate_sets_inactive_and_bumps_version(self):
        user = _user()
        later = datetime(2025, 6, 1, tzinfo=UTC)
        user.deactivate(at=later)
        self.assertFalse(user.is_active)
        self.assertEqual(user.version, 2)
        self.assertEqual(user.updated_at, later)

    def test_deactivate_idempotent_when_already_inactive(self):
        user = _user(is_active=False)
        original_version = user.version
        user.deactivate(at=datetime(2025, 6, 1, tzinfo=UTC))
        self.assertEqual(user.version, original_version)

    def test_activate_sets_active_and_bumps_version(self):
        user = _user(is_active=False)
        later = datetime(2025, 6, 1, tzinfo=UTC)
        user.activate(at=later)
        self.assertTrue(user.is_active)
        self.assertEqual(user.version, 2)
        self.assertEqual(user.updated_at, later)

    def test_activate_idempotent_when_already_active(self):
        user = _user()
        original_version = user.version
        user.activate(at=datetime(2025, 6, 1, tzinfo=UTC))
        self.assertEqual(user.version, original_version)


# --- Role Entity ---


class RoleTest(unittest.TestCase):
    def test_ordinary_role(self):
        role = _role()
        self.assertFalse(role.is_system_administrator)

    def test_system_administrator_flag(self):
        role = _role(is_system_administrator=True)
        self.assertTrue(role.is_system_administrator)

    def test_permissions_set(self):
        perms = {
            Permission(action=Action.READ, scope_code="warehouse.raw_materials"),
            Permission(action=Action.WRITE, scope_code="warehouse.raw_materials"),
        }
        role = _role(permissions=perms)
        self.assertEqual(len(role.permissions), 2)

    def test_grant_permission_adds_to_set(self):
        role = _role()
        perm = Permission(action=Action.READ, scope_code="warehouse.raw_materials")
        role.grant_permission(perm)
        self.assertIn(perm, role.permissions)

    def test_grant_permission_duplicate_raises(self):
        from access.domain.errors import DuplicateRolePermission
        perm = Permission(action=Action.READ, scope_code="warehouse.raw_materials")
        role = _role(permissions={perm})
        with self.assertRaises(DuplicateRolePermission):
            role.grant_permission(perm)

    def test_grant_permission_rejects_privileged_on_ordinary_role(self):
        from access.domain.errors import PrivilegedActionRequiresSystemAdministrator
        role = _role(is_system_administrator=False)
        perm = Permission(action=Action.MANAGE_ACCESS, scope_code="access_control")
        with self.assertRaises(PrivilegedActionRequiresSystemAdministrator):
            role.grant_permission(perm)

    def test_set_permissions_replaces_entire_set(self):
        old_perm = Permission(action=Action.READ, scope_code="warehouse.raw_materials")
        new_perms = {
            Permission(action=Action.WRITE, scope_code="warehouse.raw_materials"),
            Permission(action=Action.EDIT, scope_code="warehouse.raw_materials"),
        }
        role = _role(permissions={old_perm})
        role.set_permissions(new_perms)
        self.assertEqual(role.permissions, new_perms)
        self.assertNotIn(old_perm, role.permissions)

    def test_set_permissions_rejects_privileged_on_ordinary_role(self):
        from access.domain.errors import PrivilegedActionRequiresSystemAdministrator
        role = _role(is_system_administrator=False)
        perms = {
            Permission(action=Action.READ, scope_code="warehouse.raw_materials"),
            Permission(action=Action.MANAGE_ACCESS, scope_code="access_control"),
        }
        with self.assertRaises(PrivilegedActionRequiresSystemAdministrator):
            role.set_permissions(perms)
        # Permissions unchanged on failure
        self.assertEqual(role.permissions, set())

    def test_set_permissions_allows_privileged_on_sysadmin_role(self):
        role = _role(is_system_administrator=True)
        perms = {
            Permission(action=Action.MANAGE_ACCESS, scope_code="access_control"),
            Permission(action=Action.EDIT_OUTSIDE_WINDOW, scope_code="warehouse.raw_materials"),
        }
        role.set_permissions(perms)
        self.assertEqual(role.permissions, perms)

    def test_set_permissions_rejects_edit_outside_window_on_ordinary(self):
        from access.domain.errors import PrivilegedActionRequiresSystemAdministrator
        role = _role(is_system_administrator=False)
        perms = {Permission(action=Action.EDIT_OUTSIDE_WINDOW, scope_code="warehouse.raw_materials")}
        with self.assertRaises(PrivilegedActionRequiresSystemAdministrator):
            role.set_permissions(perms)


# --- Assignment Entity ---


class AssignmentTest(unittest.TestCase):
    def test_current_when_not_revoked(self):
        a = _assignment()
        self.assertTrue(a.is_current)
        self.assertIsNone(a.revoked_at)

    def test_not_current_when_revoked(self):
        a = Assignment(
            assignment_id="asgn-1",
            user_id="user-1",
            role_id="role-1",
            assigned_by_user_id="admin-1",
            assigned_at=NOW,
            revoked_by_user_id="admin-1",
            revoked_at=NOW,
            revoke_reason="Reassigned",
        )
        self.assertFalse(a.is_current)

    def test_revoke_sets_fields_and_marks_not_current(self):
        a = _assignment()
        later = datetime(2025, 6, 1, tzinfo=UTC)
        a.revoke(by="admin-1", reason="No longer needed", at=later)
        self.assertFalse(a.is_current)
        self.assertEqual(a.revoked_by_user_id, "admin-1")
        self.assertEqual(a.revoke_reason, "No longer needed")
        self.assertEqual(a.revoked_at, later)

    def test_revoke_already_revoked_raises(self):
        from access.domain.errors import AssignmentAlreadyRevoked
        a = Assignment(
            assignment_id="asgn-1",
            user_id="user-1",
            role_id="role-1",
            assigned_by_user_id="admin-1",
            assigned_at=NOW,
            revoked_by_user_id="admin-1",
            revoked_at=NOW,
            revoke_reason="Reassigned",
        )
        with self.assertRaises(AssignmentAlreadyRevoked):
            a.revoke(by="admin-2", reason="Retry", at=NOW)


# --- Authorization: Default Deny (Property 1) ---


class DefaultDenyTest(unittest.TestCase):
    """Property 1: if no matching permission exists, deny."""

    def test_no_assignments_denies(self):
        self.assertFalse(
            authorize(_user(), Action.READ, "warehouse.raw_materials", [], [], [_scope()])
        )

    def test_inactive_user_denies(self):
        role = _role(permissions={Permission(Action.READ, "warehouse.raw_materials")})
        self.assertFalse(
            authorize(_user(is_active=False), Action.READ, "warehouse.raw_materials",
                      [_assignment()], [role], [_scope()])
        )

    def test_inactive_role_denies(self):
        role = _role(is_active=False, permissions={Permission(Action.READ, "warehouse.raw_materials")})
        self.assertFalse(
            authorize(_user(), Action.READ, "warehouse.raw_materials",
                      [_assignment()], [role], [_scope()])
        )

    def test_inactive_scope_denies(self):
        role = _role(permissions={Permission(Action.READ, "warehouse.raw_materials")})
        self.assertFalse(
            authorize(_user(), Action.READ, "warehouse.raw_materials",
                      [_assignment()], [role], [_scope(is_active=False)])
        )

    def test_revoked_assignment_denies(self):
        role = _role(permissions={Permission(Action.READ, "warehouse.raw_materials")})
        a = _assignment()
        a.revoked_at = NOW
        self.assertFalse(
            authorize(_user(), Action.READ, "warehouse.raw_materials", [a], [role], [_scope()])
        )

    def test_wrong_action_denies(self):
        role = _role(permissions={Permission(Action.READ, "warehouse.raw_materials")})
        self.assertFalse(
            authorize(_user(), Action.WRITE, "warehouse.raw_materials",
                      [_assignment()], [role], [_scope()])
        )

    def test_unrecognized_scope_denies(self):
        role = _role(permissions={Permission(Action.READ, "warehouse.raw_materials")})
        self.assertFalse(
            authorize(_user(), Action.READ, "unknown.scope",
                      [_assignment()], [role], [_scope()])
        )


# --- Authorization: Exact Match (Property 2) ---


class ExactMatchTest(unittest.TestCase):
    """Property 2: dot-separated scope codes have no inheritance."""

    def test_prefix_does_not_authorize_sibling(self):
        role = _role(permissions={Permission(Action.READ, "yarn_spinning.section.preparation")})
        scopes = [
            _scope(scope_id="s1", scope_code="yarn_spinning.section.preparation"),
            _scope(scope_id="s2", scope_code="yarn_spinning.section.ring_spinning"),
        ]
        self.assertFalse(
            authorize(_user(), Action.READ, "yarn_spinning.section.ring_spinning",
                      [_assignment()], [role], scopes)
        )

    def test_exact_match_authorizes(self):
        role = _role(permissions={Permission(Action.READ, "yarn_spinning.section.preparation")})
        scopes = [_scope(scope_id="s1", scope_code="yarn_spinning.section.preparation")]
        self.assertTrue(
            authorize(_user(), Action.READ, "yarn_spinning.section.preparation",
                      [_assignment()], [role], scopes)
        )


# --- Authorization: Union (Property 3) ---


class UnionTest(unittest.TestCase):
    """Property 3: effective permissions = distinct union of active roles."""

    def test_multiple_roles_combine(self):
        role_a = _role(role_id="r1", permissions={Permission(Action.READ, "warehouse.raw_materials")})
        role_b = _role(role_id="r2", role_code="writer", permissions={Permission(Action.WRITE, "warehouse.raw_materials")})
        user = _user()
        assignments = [_assignment(role_id="r1"), _assignment(role_id="r2")]
        scopes = [_scope()]

        perms = effective_permissions(user, assignments, [role_a, role_b], scopes)
        self.assertEqual(len(perms), 2)
        self.assertIn(Permission(Action.READ, "warehouse.raw_materials"), perms)
        self.assertIn(Permission(Action.WRITE, "warehouse.raw_materials"), perms)


# --- Authorization: System Administrator Global Access (Property 4) ---


class SystemAdministratorTest(unittest.TestCase):
    """Property 4: active admin gets all 5 actions in every active scope."""

    def test_global_access_all_actions(self):
        admin_role = _role(role_id="admin", is_system_administrator=True)
        scopes = [
            _scope(scope_id="s1", scope_code="warehouse.raw_materials"),
            _scope(scope_id="s2", scope_code="access_control"),
        ]
        user = _user()
        assignments = [_assignment(role_id="admin")]

        perms = effective_permissions(user, assignments, [admin_role], scopes)
        # Should have 5 actions × 2 scopes = 10 permissions
        self.assertEqual(len(perms), 10)

    def test_admin_authorize_any_action_in_any_scope(self):
        admin_role = _role(role_id="admin", is_system_administrator=True)
        scopes = [_scope(scope_id="s1", scope_code="access_control")]
        user = _user()
        assignments = [_assignment(role_id="admin")]

        self.assertTrue(
            authorize(user, Action.MANAGE_ACCESS, "access_control",
                      assignments, [admin_role], scopes)
        )

    def test_admin_covers_newly_registered_scope(self):
        admin_role = _role(role_id="admin", is_system_administrator=True)
        new_scope = _scope(scope_id="new", scope_code="lot_processing.stage.dyeing")
        user = _user()
        assignments = [_assignment(role_id="admin")]

        self.assertTrue(
            authorize(user, Action.READ, "lot_processing.stage.dyeing",
                      assignments, [admin_role], [new_scope])
        )


if __name__ == "__main__":
    unittest.main()
