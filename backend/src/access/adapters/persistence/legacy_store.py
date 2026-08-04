"""Transitional repository shims for the new use cases reading the new schema.

These shims satisfy the repository protocols using direct SQLAlchemy queries
against the administration schema. They are read-only (no mutations) and exist
only until PR 4 introduces proper per-aggregate repository adapters.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from access.adapters.persistence.records import (
    AccessRolePermissionRecord,
    AccessRoleRecord,
    AccessScopeRecord,
    AccessUserRecord,
    AccessUserRoleAssignmentRecord,
)
from access.domain.actions import Action, Permission
from access.domain.roles import Assignment, Role
from access.domain.scopes import Scope
from access.domain.users import AccessUser


class UserRepositoryShim:
    """Read-only AccessUserRepository implementation against new schema."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_subject(self, identity_subject: str) -> AccessUser | None:
        row = self._session.execute(
            select(AccessUserRecord).where(
                AccessUserRecord.identity_subject == identity_subject
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def find_by_id(self, user_id: str) -> AccessUser | None:
        row = self._session.execute(
            select(AccessUserRecord).where(AccessUserRecord.user_id == user_id)
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def list_all(self) -> list[AccessUser]:
        rows = self._session.execute(
            select(AccessUserRecord).order_by(AccessUserRecord.created_at)
        ).scalars().all()
        return [self._to_domain(r) for r in rows]

    def save(self, user: AccessUser) -> None:
        raise NotImplementedError("Shim is read-only. Use PR 4 adapters.")

    def count_active_administrators(
        self, *, exclude_user_id: str | None = None, for_update: bool = False
    ) -> int:
        raise NotImplementedError("Shim is read-only. Use PR 4 adapters.")

    @staticmethod
    def _to_domain(row: AccessUserRecord) -> AccessUser:
        return AccessUser(
            user_id=str(row.user_id),
            identity_subject=row.identity_subject,
            user_code=row.user_code,
            display_name=row.display_name,
            is_active=row.is_active,
            authorization_version=row.authorization_version,
            version=row.version,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class RoleRepositoryShim:
    """Read-only RoleRepository implementation against new schema."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, role_id: str) -> Role | None:
        row = self._session.execute(
            select(AccessRoleRecord).where(AccessRoleRecord.role_id == role_id)
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def find_by_code(self, role_code: str) -> Role | None:
        row = self._session.execute(
            select(AccessRoleRecord).where(AccessRoleRecord.role_code == role_code)
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def find_system_administrator_role(self) -> Role | None:
        row = self._session.execute(
            select(AccessRoleRecord).where(
                AccessRoleRecord.is_system_administrator.is_(True)
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def list_all(self) -> list[Role]:
        rows = self._session.execute(
            select(AccessRoleRecord).order_by(AccessRoleRecord.created_at)
        ).scalars().all()
        return [self._to_domain(r) for r in rows]

    def find_assignments_for_user(self, user_id: str) -> list[Assignment]:
        rows = self._session.execute(
            select(AccessUserRoleAssignmentRecord).where(
                AccessUserRoleAssignmentRecord.user_id == user_id,
                AccessUserRoleAssignmentRecord.revoked_at.is_(None),
            )
        ).scalars().all()
        return [
            Assignment(
                assignment_id=str(r.assignment_id),
                user_id=str(r.user_id),
                role_id=str(r.role_id),
                assigned_by_user_id=str(r.assigned_by_user_id),
                assigned_at=r.assigned_at,
            )
            for r in rows
        ]

    def find_assignments_for_role(self, role_id: str) -> list[Assignment]:
        rows = self._session.execute(
            select(AccessUserRoleAssignmentRecord).where(
                AccessUserRoleAssignmentRecord.role_id == role_id,
                AccessUserRoleAssignmentRecord.revoked_at.is_(None),
            )
        ).scalars().all()
        return [
            Assignment(
                assignment_id=str(r.assignment_id),
                user_id=str(r.user_id),
                role_id=str(r.role_id),
                assigned_by_user_id=str(r.assigned_by_user_id),
                assigned_at=r.assigned_at,
            )
            for r in rows
        ]

    def save(self, role: Role) -> None:
        raise NotImplementedError("Shim is read-only. Use PR 4 adapters.")

    def save_assignment(self, assignment: Assignment) -> None:
        raise NotImplementedError("Shim is read-only. Use PR 4 adapters.")

    def _to_domain(self, row: AccessRoleRecord) -> Role:
        perm_rows = self._session.execute(
            select(AccessRolePermissionRecord).where(
                AccessRolePermissionRecord.role_id == row.role_id
            )
        ).scalars().all()

        scope_ids = {p.scope_id for p in perm_rows}
        scope_map: dict = {}
        if scope_ids:
            scope_rows = self._session.execute(
                select(AccessScopeRecord).where(
                    AccessScopeRecord.scope_id.in_(scope_ids)
                )
            ).scalars().all()
            scope_map = {r.scope_id: r.scope_code for r in scope_rows}

        permissions = {
            Permission(action=Action(p.action), scope_code=scope_map[p.scope_id])
            for p in perm_rows
            if p.scope_id in scope_map
        }

        return Role(
            role_id=str(row.role_id),
            role_code=row.role_code,
            role_name=row.role_name,
            description=row.description,
            is_system_administrator=row.is_system_administrator,
            is_active=row.is_active,
            version=row.version,
            permissions=permissions,
        )


class ScopeRepositoryShim:
    """Read-only ScopeRepository implementation against new schema."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, scope_id: str) -> Scope | None:
        row = self._session.execute(
            select(AccessScopeRecord).where(AccessScopeRecord.scope_id == scope_id)
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def find_by_code(self, scope_code: str) -> Scope | None:
        row = self._session.execute(
            select(AccessScopeRecord).where(
                AccessScopeRecord.scope_code == scope_code
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def list_all(self) -> list[Scope]:
        rows = self._session.execute(
            select(AccessScopeRecord).order_by(AccessScopeRecord.created_at)
        ).scalars().all()
        return [self._to_domain(r) for r in rows]

    def save(self, scope: Scope) -> None:
        raise NotImplementedError("Shim is read-only. Use PR 4 adapters.")

    @staticmethod
    def _to_domain(row: AccessScopeRecord) -> Scope:
        return Scope(
            scope_id=str(row.scope_id),
            definition_key=row.definition_key,
            scope_code=row.scope_code,
            scope_name=row.scope_name,
            owning_context=row.owning_context,
            description=row.description,
            is_active=row.is_active,
            version=row.version,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
