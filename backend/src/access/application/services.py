from copy import deepcopy
from dataclasses import dataclass

from access.domain.models import (
    ACCESS_CONTROL,
    WAREHOUSE_RAW_MATERIALS,
    Action,
    AccessProfile,
    AccessSnapshot,
    Role,
    RoleAssignment,
    Scope,
    ScopeCode,
    SYSTEM_ADMINISTRATOR,
    allows,
    snapshot_for,
)
from access.ports import AccessState, AccessStore, AuditCommand


class AccessDenied(Exception):
    pass


class BootstrapConflict(Exception):
    pass


class FinalAdministratorRemoval(Exception):
    pass


@dataclass(frozen=True, slots=True)
class MutationCommand:
    actor_subject: str
    target_subject: str
    reason: str
    operation_id: str


class AccessApplication:
    """Framework-free authorization and serialized policy mutation use cases."""

    def __init__(self, store: AccessStore) -> None:
        self._store = store

    def authorize(self, subject: str, action: Action, scope: ScopeCode) -> None:
        state = self._store.load()
        if not allows(self.current_access(subject, state), action, scope, state.scopes):
            raise AccessDenied("access_denied")

    def current_access(self, subject: str, state: AccessState | None = None) -> AccessSnapshot | None:
        state = state or self._store.load()
        return snapshot_for(subject, state.profiles, state.roles, state.scopes, state.assignments)

    def bootstrap(self, subject: str, profile_code: str, operation_id: str) -> AccessSnapshot:
        with self._store.serialized():
            state = self._store.load()
            existing = self.current_access(subject, state)
            if existing is not None:
                if (existing.profile_code == profile_code and existing.global_access
                        and state.bootstrap_operation_id == operation_id):
                    return existing
                raise BootstrapConflict("Bootstrap identifiers conflict with existing state.")
            if state.profiles or state.roles or state.scopes or state.assignments:
                raise BootstrapConflict("Bootstrap rejects partial state.")
            state = AccessState(
                bootstrap_operation_id=operation_id,
                profiles=[AccessProfile(subject, profile_code)],
                roles=[Role(SYSTEM_ADMINISTRATOR)],
                scopes=[Scope(ScopeCode(ACCESS_CONTROL)), Scope(ScopeCode(WAREHOUSE_RAW_MATERIALS))],
                assignments=[RoleAssignment(subject, SYSTEM_ADMINISTRATOR)],
            )
            snapshot = self.current_access(subject, state)
            assert snapshot is not None
            self._store.commit(state, AuditCommand(None, subject, "initial_bootstrap", None, operation_id, {}, {"profile_code": profile_code}))
            return snapshot

    def set_profile_active(self, command: MutationCommand, is_active: bool) -> None:
        self._mutate(command, "profile_active", lambda state: self._profile(state, command.target_subject).__setattr__("is_active", is_active))

    def set_role_active(self, command: MutationCommand, role_code: str, is_active: bool) -> None:
        self._mutate(command, "role_active", lambda state: self._role(state, role_code).__setattr__("is_active", is_active))

    def create_current_assignment(self, command: MutationCommand, role_code: str) -> None:
        self._mutate(command, "assignment_created", lambda state: state.assignments.append(RoleAssignment(command.target_subject, role_code)))

    def remove_current_assignment(self, command: MutationCommand, role_code: str) -> None:
        self._mutate(command, "assignment_removed", lambda state: state.assignments.__setitem__(slice(None), [item for item in state.assignments if not (item.subject == command.target_subject and item.role_code == role_code and item.is_current)]))

    def set_assignment_active(self, command: MutationCommand, role_code: str, is_active: bool) -> None:
        self._mutate(command, "assignment_active", lambda state: self._assignment(state, command.target_subject, role_code).__setattr__("is_active", is_active))

    def _mutate(self, command: MutationCommand, change_kind: str, mutation) -> None:
        if not command.reason:
            raise ValueError("Mutation reason is required.")
        with self._store.serialized():
            before = self._store.load()
            self.authorize(command.actor_subject, Action.WRITE, ScopeCode(ACCESS_CONTROL))
            candidate = deepcopy(before)
            mutation(candidate)
            if not self._operational_administrator_exists(candidate):
                raise FinalAdministratorRemoval("At least one operational System Administrator is required.")
            self._store.commit(candidate, AuditCommand(command.actor_subject, command.target_subject, change_kind, command.reason, command.operation_id, {"redacted": True}, {"redacted": True}))

    @staticmethod
    def _operational_administrator_exists(state: AccessState) -> bool:
        for profile in state.profiles:
            snapshot = snapshot_for(
                profile.subject,
                state.profiles,
                state.roles,
                state.scopes,
                state.assignments,
            )
            if snapshot is not None and snapshot.global_access:
                return True
        return False

    @staticmethod
    def _profile(state: AccessState, subject: str) -> AccessProfile:
        return next(item for item in state.profiles if item.subject == subject)

    @staticmethod
    def _role(state: AccessState, code: str) -> Role:
        return next(item for item in state.roles if item.code == code)

    @staticmethod
    def _assignment(state: AccessState, subject: str, role_code: str) -> RoleAssignment:
        return next(item for item in state.assignments if item.subject == subject and item.role_code == role_code and item.is_current)
