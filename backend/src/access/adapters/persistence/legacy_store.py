"""Transitional store adapter for the legacy AccessApplication.

Reads from the new access_control_administration schema and exposes
the spine-era AccessState interface. Removed in PR 4 when the
per-use-case application layer replaces the monolithic AccessApplication.
"""

from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from access.application.services import AccessState, AuditCommand
from access.domain.models import (
    AccessProfile,
    Permission,
    Role,
    RoleAssignment,
    Scope,
    ScopeCode,
    SYSTEM_ADMINISTRATOR,
)
from access.adapters.persistence.records import (
    AccessChangeAuditRecord,
    AccessRolePermissionRecord,
    AccessRoleRecord,
    AccessScopeRecord,
    AccessUserRecord,
    AccessUserRoleAssignmentRecord,
)


class LegacyStoreAdapter:
    """Adapts the new schema to the spine-era AccessStore protocol.

    Only supports the read path needed for authorize() and current_access().
    Bootstrap and mutations are not supported — they require the real
    application use cases (PR 3–4).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @contextmanager
    def serialized(self):
        yield

    def load(self) -> AccessState:
        """Load the current access state from the new schema tables."""
        # Load users as spine-era AccessProfile
        user_rows = self._session.execute(
            select(AccessUserRecord)
        ).scalars().all()
        profiles = [
            AccessProfile(
                subject=row.identity_subject,
                code=row.user_code,
                is_active=row.is_active,
            )
            for row in user_rows
        ]

        # Load roles with their permissions
        role_rows = self._session.execute(select(AccessRoleRecord)).scalars().all()
        perm_rows = self._session.execute(select(AccessRolePermissionRecord)).scalars().all()
        scope_rows = self._session.execute(select(AccessScopeRecord)).scalars().all()

        # Build scope_id → scope_code map
        scope_id_to_code = {row.scope_id: row.scope_code for row in scope_rows}

        # Build role_id → permissions
        from access.domain.models import Action
        role_perms: dict[UUID, frozenset[Permission]] = {}
        for role_row in role_rows:
            perms = frozenset(
                Permission(Action(p.action), ScopeCode(scope_id_to_code[p.scope_id]))
                for p in perm_rows
                if p.role_id == role_row.role_id and p.scope_id in scope_id_to_code
            )
            role_perms[role_row.role_id] = perms

        roles = [
            Role(
                code=SYSTEM_ADMINISTRATOR if row.is_system_administrator else row.role_code,
                permissions=role_perms.get(row.role_id, frozenset()),
                is_active=row.is_active,
            )
            for row in role_rows
        ]

        # Build scopes
        scopes = [
            Scope(code=ScopeCode(row.scope_code), is_active=row.is_active)
            for row in scope_rows
        ]

        # Load current (non-revoked) assignments
        assignment_rows = self._session.execute(
            select(AccessUserRoleAssignmentRecord).where(
                AccessUserRoleAssignmentRecord.revoked_at.is_(None)
            )
        ).scalars().all()

        # Map user_id → subject, role_id → role_code
        user_id_to_subject = {row.user_id: row.identity_subject for row in user_rows}
        role_id_to_code = {
            row.role_id: (SYSTEM_ADMINISTRATOR if row.is_system_administrator else row.role_code)
            for row in role_rows
        }

        assignments = [
            RoleAssignment(
                subject=user_id_to_subject.get(row.user_id, ""),
                role_code=role_id_to_code.get(row.role_id, ""),
                is_active=True,
                is_current=True,
            )
            for row in assignment_rows
            if row.user_id in user_id_to_subject and row.role_id in role_id_to_code
        ]

        return AccessState(
            bootstrap_operation_id=None,
            profiles=profiles,
            roles=roles,
            scopes=scopes,
            assignments=assignments,
        )

    def commit(self, state: AccessState, audit: AuditCommand) -> None:
        """Not supported in the legacy adapter. Use the new use cases."""
        raise NotImplementedError(
            "LegacyStoreAdapter does not support mutations. "
            "Use the new application use cases (PR 3–4)."
        )
