"""Behavior tests for read-only Access Control impact previews."""

import unittest
from datetime import datetime, timezone

from access.adapters.persistence.preview_query import RepositoryPreviewQuery
from access.application.preview_role_change import PreviewRoleChange
from access.application.preview_user_role_replacement import PreviewUserRoleReplacement
from access.domain.actions import Action, Permission
from access.domain.errors import AccessVersionConflict, LastSystemAdministratorRequired
from access.domain.roles import Assignment, Role
from access.domain.scopes import Scope
from access.domain.users import AccessUser


NOW = datetime(2025, 1, 1, tzinfo=timezone.utc)


class Users:
    def __init__(self, users): self.items = {user.user_id: user for user in users}
    def find_by_id(self, user_id): return self.items.get(user_id)
    def count_active_administrators(self, *, exclude_user_id=None, **_):
        return sum(user.is_active and user.user_id != exclude_user_id for user in self.items.values())


class Roles:
    def __init__(self, roles): self.items = {role.role_id: role for role in roles}
    def find_by_id(self, role_id): return self.items.get(role_id)
    def find_system_administrator_role(self): return next((role for role in self.items.values() if role.is_system_administrator), None)


class Assignments:
    def __init__(self, assignments): self.items = assignments
    def find_for_user(self, user_id): return [item for item in self.items if item.user_id == user_id and item.is_current]
    def find_for_role(self, role_id): return [item for item in self.items if item.role_id == role_id and item.is_current]


class Scopes:
    def __init__(self, scopes): self.items = scopes
    def list_all(self): return self.items


def user(user_id="user-1", version=1):
    return AccessUser(user_id, f"subject-{user_id}", f"USR-{user_id}", f"User {user_id}", True, 1, version, NOW, NOW)


def role(role_id, permissions=(), *, sysadmin=False, version=1):
    return Role(role_id, role_id, role_id, None, sysadmin, True, version, set(permissions), NOW, NOW)


def assignment(user_id, role_id):
    return Assignment(f"{user_id}-{role_id}", user_id, role_id, "admin", NOW)


def scope():
    return Scope("scope", "scope", "warehouse.raw_materials", "Scope", "Warehouse", "", True, 1, NOW, NOW)


class ImpactPreviewTest(unittest.TestCase):
    def query(self, users, roles, assignments):
        return RepositoryPreviewQuery(
            user_repository=Users(users), role_repository=Roles(roles),
            assignment_repository=Assignments(assignments), scope_repository=Scopes([scope()]),
        )

    def test_role_preview_reports_assignees_but_excludes_overlapping_removal(self):
        read = Permission(Action.READ, "warehouse.raw_materials")
        write = Permission(Action.WRITE, "warehouse.raw_materials")
        primary = role("primary", [read, write])
        overlapping = role("overlapping", [write])
        preview = PreviewRoleChange(preview_query=self.query(
            [user()], [primary, overlapping], [assignment("user-1", "primary"), assignment("user-1", "overlapping")],
        )).execute(role_id="primary", permissions={read})

        self.assertEqual(preview.subject_version, 1)
        self.assertEqual(len(preview.affected_users), 1)
        self.assertEqual([item.user_id for item in preview.affected_users], ["user-1"])
        self.assertEqual(preview.permissions_removed, frozenset())

    def test_role_preview_reports_net_permission_addition(self):
        read = Permission(Action.READ, "warehouse.raw_materials")
        write = Permission(Action.WRITE, "warehouse.raw_materials")
        preview = PreviewRoleChange(preview_query=self.query(
            [user()], [role("primary", [read])], [assignment("user-1", "primary")],
        )).execute(role_id="primary", permissions={read, write})

        self.assertEqual(preview.permissions_added, frozenset({write}))
        self.assertEqual(preview.permissions_removed, frozenset())

    def test_user_replacement_preview_is_read_only_and_guards_last_administrator(self):
        ordinary = role("ordinary", [Permission(Action.READ, "warehouse.raw_materials")])
        administrator = role("administrator", sysadmin=True)
        target = user(version=4)
        users = Users([target])
        roles = Roles([ordinary, administrator])
        assignments = Assignments([assignment("user-1", "administrator")])
        query = RepositoryPreviewQuery(
            user_repository=users, role_repository=roles, assignment_repository=assignments,
            scope_repository=Scopes([scope()]),
        )

        with self.assertRaises(LastSystemAdministratorRequired):
            PreviewUserRoleReplacement(preview_query=query).execute(user_id="user-1", role_ids=["ordinary"])
        self.assertEqual(target.version, 4)
        self.assertEqual([item.role_id for item in assignments.items], ["administrator"])

    def test_user_replacement_reports_net_permission_and_role_deltas(self):
        read = Permission(Action.READ, "warehouse.raw_materials")
        write = Permission(Action.WRITE, "warehouse.raw_materials")
        first, second, third = role("first", [read]), role("second", [write]), role("third", [read, write])
        preview = PreviewUserRoleReplacement(preview_query=self.query(
            [user()], [first, second, third], [assignment("user-1", "first"), assignment("user-1", "second")],
        )).execute(user_id="user-1", role_ids=["second", "third"])

        self.assertEqual(preview.permissions_added, frozenset())
        self.assertEqual(preview.permissions_removed, frozenset())
        self.assertEqual([item.role_id for item in preview.roles_added], ["third"])
        self.assertEqual([item.role_id for item in preview.roles_removed], ["first"])

    def test_stale_confirmation_retains_existing_version_conflict(self):
        from access.application.commands import UpdateRoleCommand
        from access.application.update_role import UpdateRole

        target = role("role", version=5)
        with self.assertRaises(AccessVersionConflict):
            UpdateRole(
                role_repository=Roles([target]), scope_repository=type("Scopes", (), {"find_by_id": lambda *_: scope()})(),
                scope_definition_registry=type("Definitions", (), {"get": lambda *_: None})(),
                audit_repository=type("Audit", (), {"append": lambda **_: None})(),
                transaction=type("Transaction", (), {"atomic": lambda _: __import__("contextlib").nullcontext()})(),
                clock=type("Clock", (), {"now": lambda _: NOW})(),
            ).execute(UpdateRoleCommand("role", "Role", None, [], 4, "test", "actor", "op"))


if __name__ == "__main__":
    unittest.main()
