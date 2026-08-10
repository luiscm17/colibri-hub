"""Unit tests for access application use cases: lifecycle, detail, and pagination.

Tests tasks 3.8, 4.4, and 5.7 from the access-spec-alignment change.
"""

import unittest
from datetime import datetime, timezone
from contextlib import contextmanager

from access.application.activate_role import ActivateRole
from access.application.activate_scope import ActivateScope
from access.application.commands import (
    ActivateRoleCommand,
    ActivateScopeCommand,
    DeactivateRoleCommand,
    DeactivateScopeCommand,
    UpdateRoleCommand,
)
from access.application.deactivate_role import DeactivateRole
from access.application.deactivate_scope import DeactivateScope
from access.application.get_access_user import GetAccessUser
from access.application.list_access_audits import ListAccessAudits
from access.application.list_access_users import ListAccessUsers
from access.application.list_roles import ListRoles
from access.application.update_role import UpdateRole
from access.domain.actions import Action, Permission
from access.domain.audit import AccessAuditEntry
from access.domain.errors import (
    AccessRoleNotFound,
    AccessScopeNotFound,
    AccessUserNotFound,
    AccessVersionConflict,
    PrivilegedActionRequiresSystemAdministrator,
    ReservedRoleMutationForbidden,
)
from access.domain.roles import Assignment, Role
from access.domain.scopes import Scope, ScopeDefinition
from access.domain.users import AccessUser

NOW = datetime(2025, 6, 1, tzinfo=timezone.utc)


# --- Fakes ---


class FakeClock:
    def now(self):
        return NOW


class FakeIdentity:
    _counter = 0

    def generate_id(self):
        self._counter += 1
        return f"gen-id-{self._counter}"

    def generate_operation_id(self):
        self._counter += 1
        return f"op-{self._counter}"


class FakeTransaction:
    @contextmanager
    def atomic(self):
        yield


class FakeAuditRepo:
    def __init__(self):
        self.entries: list[dict] = []

    def append(self, **kwargs):
        self.entries.append(kwargs)

    def list_recent(self, *, limit=50, offset=0, **kwargs):
        return []

    def count(self, **kwargs):
        return 0


class FakeRoleRepo:
    def __init__(self, roles: list[Role] | None = None):
        self.roles: dict[str, Role] = {r.role_id: r for r in (roles or [])}

    def find_by_id(self, role_id):
        return self.roles.get(role_id)

    def find_by_code(self, code):
        return next((r for r in self.roles.values() if r.role_code == code), None)

    def find_system_administrator_role(self):
        return next((r for r in self.roles.values() if r.is_system_administrator), None)

    def list_all(self, *, limit=None, offset=0):
        items = list(self.roles.values())
        if offset:
            items = items[offset:]
        if limit is not None:
            items = items[:limit]
        return items

    def count(self):
        return len(self.roles)

    def save(self, role, **kwargs):
        self.roles[role.role_id] = role


class FakeScopeRepo:
    def __init__(self, scopes: list[Scope] | None = None):
        self.scopes: dict[str, Scope] = {s.scope_id: s for s in (scopes or [])}

    def find_by_id(self, scope_id):
        return self.scopes.get(scope_id)

    def find_by_code(self, code):
        return next((s for s in self.scopes.values() if s.scope_code == code), None)

    def list_all(self, *, limit=None, offset=0):
        items = list(self.scopes.values())
        if offset:
            items = items[offset:]
        if limit is not None:
            items = items[:limit]
        return items

    def count(self):
        return len(self.scopes)

    def save(self, scope):
        self.scopes[scope.scope_id] = scope


class FakeScopeDefinitionRegistry:
    def __init__(self, definitions: list[ScopeDefinition] | None = None):
        self._defs = {d.definition_key: d for d in (definitions or [])}

    def all(self):
        return list(self._defs.values())

    def get(self, key):
        return self._defs.get(key)


class FakeUserRepo:
    def __init__(self, users: list[AccessUser] | None = None):
        self.users: dict[str, AccessUser] = {u.user_id: u for u in (users or [])}

    def find_by_id(self, user_id):
        return self.users.get(user_id)

    def find_by_subject(self, subject):
        return next((u for u in self.users.values() if u.identity_subject == subject), None)

    def list_all(self, *, limit=None, offset=0):
        items = list(self.users.values())
        if offset:
            items = items[offset:]
        if limit is not None:
            items = items[:limit]
        return items

    def count(self):
        return len(self.users)

    def save(self, user):
        self.users[user.user_id] = user

    def count_active_administrators(self, **kwargs):
        return 1


class FakeAssignmentRepo:
    def __init__(self, assignments: list[Assignment] | None = None):
        self._assignments = assignments or []

    def find_for_user(self, user_id):
        return [a for a in self._assignments if a.user_id == user_id and a.is_current]


# --- Helpers ---


def _scope(scope_id="scope-1", code="warehouse.raw_materials", is_active=True):
    return Scope(
        scope_id=scope_id, definition_key=code, scope_code=code,
        scope_name="Test Scope", owning_context="Test", description="desc",
        is_active=is_active, version=1, created_at=NOW, updated_at=NOW,
    )


def _role(role_id="role-1", code="reader", is_sysadmin=False, is_active=True, permissions=None, version=1):
    return Role(
        role_id=role_id, role_code=code, role_name="Test Role",
        description=None, is_system_administrator=is_sysadmin,
        is_active=is_active, version=version, permissions=permissions or set(),
        created_at=NOW, updated_at=NOW,
    )


def _user(user_id="user-1", is_active=True):
    return AccessUser(
        user_id=user_id, identity_subject=f"sub-{user_id}",
        user_code=f"USR-{user_id}", display_name="Test User",
        is_active=is_active, authorization_version=1, version=1,
        created_at=NOW, updated_at=NOW,
    )


def _definition(key="warehouse.raw_materials", actions=None):
    return ScopeDefinition(
        definition_key=key, scope_code=key, scope_name="Test",
        owning_context="Test", description="desc",
        supported_actions=frozenset(actions or [Action.READ, Action.WRITE]),
    )


def _permission_input(action="read", scope_id="scope-1"):
    from access.application.commands import PermissionInput
    return PermissionInput(action=action, scope_id=scope_id)


# ============================================================
# Task 3.8: Role & Scope Lifecycle Tests
# ============================================================


class TestUpdateRole(unittest.TestCase):
    def _make_use_case(self, roles=None, scopes=None, definitions=None):
        self.role_repo = FakeRoleRepo(roles)
        self.scope_repo = FakeScopeRepo(scopes)
        self.definition_registry = FakeScopeDefinitionRegistry(definitions)
        self.audit_repo = FakeAuditRepo()
        return UpdateRole(
            role_repository=self.role_repo,
            scope_repository=self.scope_repo,
            scope_definition_registry=self.definition_registry,
            audit_repository=self.audit_repo,
            transaction=FakeTransaction(),
            clock=FakeClock(),
        )

    def test_happy_path_updates_role(self):
        scope = _scope()
        role = _role(permissions={Permission(action=Action.READ, scope_code="warehouse.raw_materials")})
        defn = _definition()
        uc = self._make_use_case([role], [scope], [defn])

        result = uc.execute(UpdateRoleCommand(
            role_id="role-1", role_name="Updated", description="New desc",
            permissions=[_permission_input("write", "scope-1")],
            expected_version=1, reason="test", actor_user_id="admin-1", operation_id="op-1",
        ))

        self.assertEqual(result.role_name, "Updated")
        self.assertEqual(result.version, 2)
        self.assertEqual(len(result.permissions), 1)
        self.assertEqual(result.permissions[0].action, "write")
        self.assertEqual(len(self.audit_repo.entries), 1)
        self.assertEqual(self.audit_repo.entries[0]["change_kind"], "role_updated")

    def test_version_conflict_raises(self):
        role = _role(version=3)
        uc = self._make_use_case([role], [_scope()], [_definition()])

        with self.assertRaises(AccessVersionConflict):
            uc.execute(UpdateRoleCommand(
                role_id="role-1", role_name="X", description=None,
                permissions=[], expected_version=1, reason="test",
                actor_user_id="admin-1", operation_id="op-1",
            ))

    def test_not_found_raises(self):
        uc = self._make_use_case([], [_scope()], [_definition()])

        with self.assertRaises(AccessRoleNotFound):
            uc.execute(UpdateRoleCommand(
                role_id="missing", role_name="X", description=None,
                permissions=[], expected_version=1, reason="test",
                actor_user_id="admin-1", operation_id="op-1",
            ))

    def test_reserved_role_rejects_update(self):
        role = _role(is_sysadmin=True)
        uc = self._make_use_case([role], [_scope()], [_definition()])

        with self.assertRaises(ReservedRoleMutationForbidden):
            uc.execute(UpdateRoleCommand(
                role_id="role-1", role_name="Hacked", description=None,
                permissions=[], expected_version=1, reason="test",
                actor_user_id="admin-1", operation_id="op-1",
            ))

    def test_privileged_action_rejects(self):
        scope = _scope()
        role = _role()
        defn = _definition(actions=[Action.READ, Action.WRITE, Action.MANAGE_ACCESS])
        uc = self._make_use_case([role], [scope], [defn])

        with self.assertRaises(PrivilegedActionRequiresSystemAdministrator):
            uc.execute(UpdateRoleCommand(
                role_id="role-1", role_name="X", description=None,
                permissions=[_permission_input("manage_access", "scope-1")],
                expected_version=1, reason="test",
                actor_user_id="admin-1", operation_id="op-1",
            ))


class TestActivateRole(unittest.TestCase):
    def test_activates_inactive_role(self):
        role = _role(is_active=False)
        role_repo = FakeRoleRepo([role])
        audit_repo = FakeAuditRepo()
        uc = ActivateRole(
            role_repository=role_repo, audit_repository=audit_repo,
            transaction=FakeTransaction(), clock=FakeClock(),
        )

        uc.execute(ActivateRoleCommand(
            role_id="role-1", expected_version=1, reason="test",
            actor_user_id="admin-1", operation_id="op-1",
        ))

        self.assertTrue(role_repo.roles["role-1"].is_active)
        self.assertEqual(len(audit_repo.entries), 1)
        self.assertEqual(audit_repo.entries[0]["change_kind"], "role_activated")

    def test_not_found_raises(self):
        uc = ActivateRole(
            role_repository=FakeRoleRepo(), audit_repository=FakeAuditRepo(),
            transaction=FakeTransaction(), clock=FakeClock(),
        )
        with self.assertRaises(AccessRoleNotFound):
            uc.execute(ActivateRoleCommand(
                role_id="missing", expected_version=1, reason="test",
                actor_user_id="admin-1", operation_id="op-1",
            ))

    def test_version_conflict_raises(self):
        role = _role(version=5)
        uc = ActivateRole(
            role_repository=FakeRoleRepo([role]), audit_repository=FakeAuditRepo(),
            transaction=FakeTransaction(), clock=FakeClock(),
        )
        with self.assertRaises(AccessVersionConflict):
            uc.execute(ActivateRoleCommand(
                role_id="role-1", expected_version=1, reason="test",
                actor_user_id="admin-1", operation_id="op-1",
            ))


class TestDeactivateRole(unittest.TestCase):
    def test_deactivates_active_role(self):
        role = _role(is_active=True)
        role_repo = FakeRoleRepo([role])
        audit_repo = FakeAuditRepo()
        uc = DeactivateRole(
            role_repository=role_repo, audit_repository=audit_repo,
            transaction=FakeTransaction(), clock=FakeClock(),
        )

        uc.execute(DeactivateRoleCommand(
            role_id="role-1", expected_version=1, reason="test",
            actor_user_id="admin-1", operation_id="op-1",
        ))

        self.assertFalse(role_repo.roles["role-1"].is_active)
        self.assertEqual(audit_repo.entries[0]["change_kind"], "role_deactivated")

    def test_reserved_role_rejects(self):
        role = _role(is_sysadmin=True)
        uc = DeactivateRole(
            role_repository=FakeRoleRepo([role]), audit_repository=FakeAuditRepo(),
            transaction=FakeTransaction(), clock=FakeClock(),
        )
        with self.assertRaises(ReservedRoleMutationForbidden):
            uc.execute(DeactivateRoleCommand(
                role_id="role-1", expected_version=1, reason="test",
                actor_user_id="admin-1", operation_id="op-1",
            ))


class TestActivateScope(unittest.TestCase):
    def test_activates_inactive_scope(self):
        scope = _scope(is_active=False)
        scope_repo = FakeScopeRepo([scope])
        audit_repo = FakeAuditRepo()
        uc = ActivateScope(
            scope_repository=scope_repo, audit_repository=audit_repo,
            transaction=FakeTransaction(), clock=FakeClock(),
        )

        uc.execute(ActivateScopeCommand(
            scope_id="scope-1", expected_version=1, reason="test",
            actor_user_id="admin-1", operation_id="op-1",
        ))

        self.assertTrue(scope_repo.scopes["scope-1"].is_active)
        self.assertEqual(audit_repo.entries[0]["change_kind"], "scope_activated")

    def test_not_found_raises(self):
        uc = ActivateScope(
            scope_repository=FakeScopeRepo(), audit_repository=FakeAuditRepo(),
            transaction=FakeTransaction(), clock=FakeClock(),
        )
        with self.assertRaises(AccessScopeNotFound):
            uc.execute(ActivateScopeCommand(
                scope_id="missing", expected_version=1, reason="test",
                actor_user_id="admin-1", operation_id="op-1",
            ))


class TestDeactivateScope(unittest.TestCase):
    def test_deactivates_active_scope(self):
        scope = _scope(is_active=True)
        scope_repo = FakeScopeRepo([scope])
        audit_repo = FakeAuditRepo()
        uc = DeactivateScope(
            scope_repository=scope_repo, audit_repository=audit_repo,
            transaction=FakeTransaction(), clock=FakeClock(),
        )

        uc.execute(DeactivateScopeCommand(
            scope_id="scope-1", expected_version=1, reason="test",
            actor_user_id="admin-1", operation_id="op-1",
        ))

        self.assertFalse(scope_repo.scopes["scope-1"].is_active)
        self.assertEqual(audit_repo.entries[0]["change_kind"], "scope_deactivated")

    def test_version_conflict_raises(self):
        scope = _scope()
        # Create scope with version=7 to trigger conflict with expected_version=1
        scope_v7 = Scope(
            scope_id="scope-1", definition_key="warehouse.raw_materials",
            scope_code="warehouse.raw_materials", scope_name="Test Scope",
            owning_context="Test", description="desc",
            is_active=True, version=7, created_at=NOW, updated_at=NOW,
        )
        uc = DeactivateScope(
            scope_repository=FakeScopeRepo([scope_v7]), audit_repository=FakeAuditRepo(),
            transaction=FakeTransaction(), clock=FakeClock(),
        )
        with self.assertRaises(AccessVersionConflict):
            uc.execute(DeactivateScopeCommand(
                scope_id="scope-1", expected_version=1, reason="test",
                actor_user_id="admin-1", operation_id="op-1",
            ))


# ============================================================
# Task 4.4: GetAccessUser Tests
# ============================================================


class TestGetAccessUser(unittest.TestCase):
    def test_happy_path_returns_detail(self):
        user = _user()
        role = _role(permissions={Permission(action=Action.READ, scope_code="warehouse.raw_materials")})
        scope = _scope()
        assignment = Assignment(
            assignment_id="asgn-1", user_id="user-1", role_id="role-1",
            assigned_by_user_id="admin-1", assigned_at=NOW,
        )

        uc = GetAccessUser(
            user_repository=FakeUserRepo([user]),
            role_repository=FakeRoleRepo([role]),
            assignment_repository=FakeAssignmentRepo([assignment]),
            scope_repository=FakeScopeRepo([scope]),
        )

        result = uc.execute(user_id="user-1")
        self.assertEqual(result.user.user_id, "user-1")
        self.assertEqual(len(result.roles), 1)
        self.assertEqual(result.roles[0].code, "reader")
        self.assertEqual(len(result.assignments), 1)
        self.assertFalse(result.is_global)
        self.assertEqual(len(result.permissions), 1)

    def test_not_found_raises(self):
        uc = GetAccessUser(
            user_repository=FakeUserRepo(),
            role_repository=FakeRoleRepo(),
            assignment_repository=FakeAssignmentRepo(),
            scope_repository=FakeScopeRepo(),
        )
        with self.assertRaises(AccessUserNotFound):
            uc.execute(user_id="missing")

    def test_sysadmin_is_global(self):
        user = _user()
        role = _role(is_sysadmin=True)
        scope = _scope()
        assignment = Assignment(
            assignment_id="asgn-1", user_id="user-1", role_id="role-1",
            assigned_by_user_id="admin-1", assigned_at=NOW,
        )

        uc = GetAccessUser(
            user_repository=FakeUserRepo([user]),
            role_repository=FakeRoleRepo([role]),
            assignment_repository=FakeAssignmentRepo([assignment]),
            scope_repository=FakeScopeRepo([scope]),
        )

        result = uc.execute(user_id="user-1")
        self.assertTrue(result.is_global)


# ============================================================
# Task 5.7: Pagination Tests
# ============================================================


class TestListAccessUsersPagination(unittest.TestCase):
    def test_pagination_total_preserving(self):
        users = [_user(f"u-{i}") for i in range(5)]
        user_repo = FakeUserRepo(users)
        uc = ListAccessUsers(user_repository=user_repo)

        result = uc.execute(page=1, page_size=2)
        self.assertEqual(result.total, 5)
        self.assertEqual(len(result.items), 2)

    def test_page_2_returns_next_slice(self):
        users = [_user(f"u-{i}") for i in range(5)]
        user_repo = FakeUserRepo(users)
        uc = ListAccessUsers(user_repository=user_repo)

        page1 = uc.execute(page=1, page_size=2)
        page2 = uc.execute(page=2, page_size=2)
        self.assertNotEqual(page1.items[0].user_id, page2.items[0].user_id)

    def test_last_page_partial(self):
        users = [_user(f"u-{i}") for i in range(3)]
        user_repo = FakeUserRepo(users)
        uc = ListAccessUsers(user_repository=user_repo)

        result = uc.execute(page=2, page_size=2)
        self.assertEqual(result.total, 3)
        self.assertEqual(len(result.items), 1)


class TestListRolesPagination(unittest.TestCase):
    def test_pagination_total_preserving(self):
        roles = [_role(f"r-{i}", code=f"code-{i}") for i in range(4)]
        role_repo = FakeRoleRepo(roles)
        uc = ListRoles(role_repository=role_repo)

        result = uc.execute(page=1, page_size=2)
        self.assertEqual(result.total, 4)
        self.assertEqual(len(result.items), 2)


class TestListAuditsPagination(unittest.TestCase):
    def test_empty_returns_zero_total(self):
        audit_repo = FakeAuditRepo()
        uc = ListAccessAudits(audit_repository=audit_repo)

        result = uc.execute(page=1, page_size=50)
        self.assertEqual(result.total, 0)
        self.assertEqual(len(result.items), 0)


if __name__ == "__main__":
    unittest.main()
