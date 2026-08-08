"""Behavior tests for role presets and authorization-version fan-out."""
import asyncio
import json
import unittest
from contextlib import contextmanager
from datetime import datetime, timezone
from access.application.change_role_preset_status import ChangeRolePresetStatus
from access.application.commands import ChangeRolePresetStatusCommand, CreateRoleFromPresetCommand, CreateRolePresetCommand, PermissionInput, UpdateRolePresetCommand
from access.application.create_role_from_preset import CreateRoleFromPreset
from access.application.create_role_preset import CreateRolePreset
from access.application.update_role_preset import UpdateRolePreset
from access.application.update_role import UpdateRole
from access.application.activate_role import ActivateRole
from access.application.deactivate_scope import DeactivateScope
from access.application.commands import ActivateRoleCommand, DeactivateScopeCommand
from access.adapters.http.error_handlers import access_error_handler
from access.domain.actions import Action, Permission
from access.domain.errors import DuplicatePresetCode, InactiveAccessPreset, PrivilegedActionRequiresSystemAdministrator
from access.domain.presets import RolePreset
from access.domain.roles import Role
from access.domain.scopes import Scope, ScopeDefinition

NOW = datetime(2025, 1, 1, tzinfo=timezone.utc)
class Clock:
    def now(self): return NOW
class Identity:
    n = 0
    def generate_id(self): self.n += 1; return f"id-{self.n}"
class Tx:
    @contextmanager
    def atomic(self): yield
class Audit:
    def __init__(self): self.entries = []
    def append(self, **entry): self.entries.append(entry)
class Presets:
    def __init__(self): self.items = {}
    def find_by_id(self, id): return self.items.get(id)
    def find_by_code(self, code): return next((p for p in self.items.values() if p.preset_code == code), None)
    def save(self, preset, **_): self.items[preset.preset_id] = preset
    def list_all(self, **_): return list(self.items.values())
    def count(self): return len(self.items)
class Roles:
    def __init__(self): self.items = {}
    def find_by_id(self, id): return self.items.get(id)
    def find_by_code(self, code): return next((r for r in self.items.values() if r.role_code == code), None)
    def save(self, role, **_): self.items[role.role_id] = role
class Scopes:
    def __init__(self): self.scope = Scope("scope", "scope", "warehouse.raw_materials", "Scope", "Warehouse", "", True, 1, NOW, NOW)
    def find_by_id(self, id): return self.scope if id == "scope" else None
    def save(self, scope): self.scope = scope
class Definitions:
    def get(self, _): return ScopeDefinition("scope", "warehouse.raw_materials", "Scope", "Warehouse", "", frozenset({Action.READ, Action.WRITE}))
class Users:
    def __init__(self): self.roles = []; self.scopes = []
    def bump_authorization_version_for_role(self, id): self.roles.append(id); return []
    def bump_authorization_version_for_scope(self, id): self.scopes.append(id); return []

class RolePresetTest(unittest.TestCase):
    def setUp(self): self.presets, self.roles, self.audit, self.identity = Presets(), Roles(), Audit(), Identity()
    def create(self, code="preset", permissions=None):
        return CreateRolePreset(preset_repository=self.presets, scope_repository=Scopes(), scope_definition_registry=Definitions(), audit_repository=self.audit, transaction=Tx(), clock=Clock(), identity=self.identity).execute(CreateRolePresetCommand(code, "Preset", None, permissions or [PermissionInput("read", "scope")], "test", "actor", "op"))
    def test_create_rejects_privileged_and_duplicate_codes(self):
        with self.assertRaises(PrivilegedActionRequiresSystemAdministrator): self.create(permissions=[PermissionInput("manage_access", "scope")])
        self.create()
        with self.assertRaises(DuplicatePresetCode): self.create()
    def test_update_replaces_permissions_and_snapshot_role_is_independent(self):
        preset = self.create(); role = CreateRoleFromPreset(preset_repository=self.presets, role_repository=self.roles, audit_repository=self.audit, transaction=Tx(), clock=Clock(), identity=self.identity).execute(CreateRoleFromPresetCommand(preset.preset_id, "role", "Role", None, "test", "actor", "op"))
        UpdateRolePreset(preset_repository=self.presets, scope_repository=Scopes(), scope_definition_registry=Definitions(), audit_repository=self.audit, transaction=Tx(), clock=Clock()).execute(UpdateRolePresetCommand(preset.preset_id, "Changed", None, [], 1, "test", "actor", "op"))
        self.assertEqual(len(self.roles.items[role.role_id].permissions), 1); self.assertEqual(len(self.presets.items[preset.preset_id].permissions), 0)
    def test_inactive_preset_cannot_create_role(self):
        preset = self.create(); ChangeRolePresetStatus(preset_repository=self.presets, audit_repository=self.audit, transaction=Tx(), clock=Clock()).execute(ChangeRolePresetStatusCommand(preset.preset_id, False, 1, "test", "actor", "op"))
        with self.assertRaises(InactiveAccessPreset): CreateRoleFromPreset(preset_repository=self.presets, role_repository=self.roles, audit_repository=self.audit, transaction=Tx(), clock=Clock(), identity=self.identity).execute(CreateRoleFromPresetCommand(preset.preset_id, "role", "Role", None, "test", "actor", "op"))

    def test_duplicate_preset_code_maps_to_conflict_error_envelope(self):
        response = asyncio.run(access_error_handler(None, DuplicatePresetCode()))

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            json.loads(response.body)["error"]["code"],
            "duplicate_access_preset_code",
        )

class AuthorizationVersionFanoutTest(unittest.TestCase):
    def test_role_update_requests_fanout_for_assigned_role(self):
        role = Role("role", "role", "Role", None, False, True, 1, {Permission(Action.READ, "warehouse.raw_materials")}, NOW, NOW); roles, users = Roles(), Users(); roles.save(role)
        UpdateRole(role_repository=roles, scope_repository=Scopes(), scope_definition_registry=Definitions(), audit_repository=Audit(), transaction=Tx(), clock=Clock(), user_repository=users).execute(__import__("access.application.commands", fromlist=["UpdateRoleCommand"]).UpdateRoleCommand("role", "Role", None, [PermissionInput("read", "scope")], 1, "test", "actor", "op"))
        self.assertEqual(users.roles, ["role"])
    def test_role_status_and_scope_status_request_fanout(self):
        role = Role("role", "role", "Role", None, False, False, 1, set(), NOW, NOW); roles, users, audit = Roles(), Users(), Audit(); roles.save(role)
        ActivateRole(role_repository=roles, audit_repository=audit, transaction=Tx(), clock=Clock(), user_repository=users).execute(ActivateRoleCommand("role", 1, "test", "actor", "op"))
        scope_repo = Scopes()
        DeactivateScope(scope_repository=scope_repo, audit_repository=audit, transaction=Tx(), clock=Clock(), user_repository=users).execute(DeactivateScopeCommand("scope", 1, "test", "actor", "op"))
        self.assertEqual(users.roles, ["role"]); self.assertEqual(users.scopes, ["scope"])

if __name__ == "__main__": unittest.main()
