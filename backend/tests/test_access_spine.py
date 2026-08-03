from contextlib import nullcontext
from copy import deepcopy
import unittest

from access.application.services import AccessApplication, AccessDenied, BootstrapConflict, FinalAdministratorRemoval, MutationCommand
from access.domain.models import ACCESS_CONTROL, WAREHOUSE_RAW_MATERIALS, Action, AccessProfile, Permission, Role, RoleAssignment, Scope, ScopeCode, SYSTEM_ADMINISTRATOR
from access.ports import AccessState


class Store:
    def __init__(self, state=None): self.state, self.audits = state or AccessState(), []
    def serialized(self): return nullcontext()
    def load(self): return self.state
    def commit(self, state, audit): self.state, self.audits = state, [*self.audits, audit]


class AccessSpineTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.app = AccessApplication(self.store)
        self.app.bootstrap("admin", "ADMIN", "bootstrap-1")

    def command(self, target="admin"):
        return MutationCommand("admin", target, "required operational reason", "operation-1")

    def test_bootstrap_is_idempotent_and_rejects_partial_or_conflict(self):
        retry = self.app.bootstrap("admin", "ADMIN", "bootstrap-1")
        self.assertTrue(retry.global_access)
        self.assertEqual(len(self.store.audits), 1)
        with self.assertRaises(BootstrapConflict): self.app.bootstrap("admin", "OTHER", "operation-2")
        with self.assertRaises(BootstrapConflict): self.app.bootstrap("admin", "ADMIN", "operation-2")
        partial = AccessApplication(Store(AccessState(scopes=[Scope(ScopeCode(ACCESS_CONTROL))])))
        with self.assertRaises(BootstrapConflict): partial.bootstrap("other", "OTHER", "operation-3")

    def test_exact_additive_active_policy_and_ordinary_non_global_snapshot(self):
        state = AccessState(
            profiles=[AccessProfile("ordinary", "ORD")],
            roles=[Role("reader", frozenset({Permission(Action.READ, ScopeCode(ACCESS_CONTROL))})), Role("writer", frozenset({Permission(Action.WRITE, ScopeCode(WAREHOUSE_RAW_MATERIALS))}))],
            scopes=[Scope(ScopeCode(ACCESS_CONTROL)), Scope(ScopeCode(WAREHOUSE_RAW_MATERIALS))],
            assignments=[RoleAssignment("ordinary", "reader"), RoleAssignment("ordinary", "writer")],
        )
        app = AccessApplication(Store(state))
        self.assertFalse(app.current_access("ordinary").global_access)
        app.authorize("ordinary", Action.READ, ScopeCode(ACCESS_CONTROL))
        app.authorize("ordinary", Action.WRITE, ScopeCode(WAREHOUSE_RAW_MATERIALS))
        with self.assertRaises(AccessDenied): app.authorize("ordinary", Action.WRITE, ScopeCode(ACCESS_CONTROL))

    def test_inactive_paths_and_missing_subject_default_deny(self):
        for path in ("profile", "role", "assignment", "scope"):
            with self.subTest(path=path):
                state = deepcopy(self.store.state)
                getattr(state, f"{path}s" if path != "assignment" else "assignments")[0].is_active = False
                with self.assertRaises(AccessDenied): AccessApplication(Store(state)).authorize("admin", Action.WRITE, ScopeCode(ACCESS_CONTROL))
        with self.assertRaises(AccessDenied): self.app.authorize("missing", Action.READ, ScopeCode(ACCESS_CONTROL))

    def test_global_admin_allows_recognized_future_scope_only(self):
        self.store.state.scopes.append(Scope(ScopeCode("future.scope")))
        self.app.authorize("admin", Action.WRITE, ScopeCode("future.scope"))
        with self.assertRaises(AccessDenied): self.app.authorize("admin", Action.WRITE, ScopeCode("unknown.scope"))

    def test_accepted_mutations_create_redacted_audit(self):
        self.app.create_current_assignment(self.command(), SYSTEM_ADMINISTRATOR)
        audit = self.store.audits[-1]
        self.assertEqual(audit.actor_subject, "admin")
        self.assertEqual(audit.reason, "required operational reason")
        self.assertEqual(audit.before, {"redacted": True})
        self.assertEqual(audit.after, {"redacted": True})

    def test_every_final_administrator_removal_path_rejects_unchanged(self):
        operations = (
            lambda: self.app.set_profile_active(self.command(), False),
            lambda: self.app.set_role_active(self.command(), SYSTEM_ADMINISTRATOR, False),
            lambda: self.app.remove_current_assignment(self.command(), SYSTEM_ADMINISTRATOR),
            lambda: self.app.set_assignment_active(self.command(), SYSTEM_ADMINISTRATOR, False),
        )
        for operation in operations:
            with self.subTest(operation=operation):
                before = deepcopy(self.store.state)
                with self.assertRaises(FinalAdministratorRemoval): operation()
                self.assertEqual(self.store.state, before)

    def test_non_final_removal_succeeds_and_unauthorized_actor_is_denied(self):
        self.store.state.profiles.append(AccessProfile("other", "OTHER"))
        self.store.state.assignments.append(RoleAssignment("other", SYSTEM_ADMINISTRATOR))
        self.app.remove_current_assignment(self.command(), SYSTEM_ADMINISTRATOR)
        self.assertTrue(self.app.current_access("other").global_access)
        self.store.state.profiles.append(AccessProfile("stranger", "STRANGER"))
        with self.assertRaises(AccessDenied): self.app.set_profile_active(MutationCommand("stranger", "stranger", "reason", "operation-2"), False)
