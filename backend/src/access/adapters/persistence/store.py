from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.orm import Session

from access.domain.models import AccessProfile, Action, Permission, Role, RoleAssignment, Scope, ScopeCode, SYSTEM_ADMINISTRATOR
from access.ports import AccessState, AuditCommand
from access.adapters.persistence.records import AccessBootstrapLockRecord, AccessChangeAuditRecord, AccessProfileRecord, AccessRoleAssignmentRecord, AccessRolePermissionRecord, AccessRoleRecord, AccessScopeRecord


class AccessStoreAdapter:
    """Maps the framework-free Access state to one serialized persistence transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @contextmanager
    def serialized(self) -> Iterator[None]:
        with self._session.begin():
            self._session.execute(select(AccessBootstrapLockRecord).where(AccessBootstrapLockRecord.id == 1).with_for_update()).scalar_one()
            role = self._session.execute(select(AccessRoleRecord).where(AccessRoleRecord.code == SYSTEM_ADMINISTRATOR).with_for_update()).scalar_one_or_none()
            if role is not None:
                self._session.execute(select(AccessRoleAssignmentRecord).where(AccessRoleAssignmentRecord.role_id == role.id, AccessRoleAssignmentRecord.is_current).with_for_update()).all()
                self._session.execute(select(AccessProfileRecord).join(AccessRoleAssignmentRecord, AccessRoleAssignmentRecord.profile_id == AccessProfileRecord.id).where(AccessRoleAssignmentRecord.role_id == role.id, AccessRoleAssignmentRecord.is_current).order_by(AccessProfileRecord.id).with_for_update()).all()
            yield

    def load(self) -> AccessState:
        profiles = self._session.execute(select(AccessProfileRecord)).scalars().all()
        roles = self._session.execute(select(AccessRoleRecord)).scalars().all()
        scopes = self._session.execute(select(AccessScopeRecord)).scalars().all()
        permissions = self._session.execute(select(AccessRolePermissionRecord)).scalars().all()
        assignments = self._session.execute(select(AccessRoleAssignmentRecord)).scalars().all()
        role_codes = {row.id: row.code for row in roles}; scope_codes = {row.id: ScopeCode(row.code) for row in scopes}; subjects = {row.id: row.subject for row in profiles}
        return AccessState(
            bootstrap_operation_id=self._session.execute(select(AccessChangeAuditRecord.operation_id).where(AccessChangeAuditRecord.change_kind == "initial_bootstrap")).scalar_one_or_none(),
            profiles=[AccessProfile(row.subject, row.code, row.is_active) for row in profiles],
            roles=[Role(row.code, frozenset(Permission(Action(item.action), scope_codes[item.scope_id]) for item in permissions if item.role_id == row.id), row.is_active) for row in roles],
            scopes=[Scope(ScopeCode(row.code), row.is_active) for row in scopes],
            assignments=[RoleAssignment(subjects[row.profile_id], role_codes[row.role_id], row.is_active, row.is_current) for row in assignments],
        )

    def commit(self, state: AccessState, audit: AuditCommand) -> None:
        profiles = {row.subject: row for row in self._session.execute(select(AccessProfileRecord)).scalars()}
        roles = {row.code: row for row in self._session.execute(select(AccessRoleRecord)).scalars()}; scopes = {row.code: row for row in self._session.execute(select(AccessScopeRecord)).scalars()}
        for item in state.profiles:
            row = profiles.setdefault(item.subject, AccessProfileRecord(subject=item.subject, code=item.code)); row.code, row.is_active = item.code, item.is_active; self._session.add(row)
        for item in state.roles:
            row = roles.setdefault(item.code, AccessRoleRecord(code=item.code)); row.is_active = item.is_active; self._session.add(row)
        for item in state.scopes:
            row = scopes.setdefault(item.code.value, AccessScopeRecord(code=item.code.value)); row.is_active = item.is_active; self._session.add(row)
        self._session.flush()
        existing_permissions = self._session.execute(select(AccessRolePermissionRecord)).scalars().all()
        wanted = {(roles[role.code].id, permission.action.value, scopes[permission.scope.value].id) for role in state.roles for permission in role.permissions}
        for row in existing_permissions:
            if (row.role_id, row.action, row.scope_id) not in wanted: self._session.delete(row)
        present = {(row.role_id, row.action, row.scope_id) for row in existing_permissions}
        for role_id, action, scope_id in wanted - present: self._session.add(AccessRolePermissionRecord(role_id=role_id, action=action, scope_id=scope_id))
        profiles_by_id = {row.id: row for row in profiles.values()}; roles_by_id = {row.id: row for row in roles.values()}
        existing_assignments = {(profiles_by_id[row.profile_id].subject, roles_by_id[row.role_id].code): row for row in self._session.execute(select(AccessRoleAssignmentRecord)).scalars()}
        wanted_assignments = {(item.subject, item.role_code): item for item in state.assignments}
        for key, row in existing_assignments.items():
            item = wanted_assignments.get(key); row.is_current, row.is_active = (False, row.is_active) if item is None else (item.is_current, item.is_active)
        for key, item in wanted_assignments.items():
            if key not in existing_assignments: self._session.add(AccessRoleAssignmentRecord(profile_id=profiles[item.subject].id, role_id=roles[item.role_code].id, is_active=item.is_active, is_current=item.is_current))
        self._session.flush()
        self._session.add(AccessChangeAuditRecord(actor_profile_id=profiles[audit.actor_subject].id if audit.actor_subject else None, affected_profile_id=profiles[audit.affected_subject].id, change_kind=audit.change_kind, reason=audit.reason, operation_id=audit.operation_id, before=audit.before, after=audit.after))
