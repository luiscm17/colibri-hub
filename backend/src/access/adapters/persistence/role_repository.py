"""Repository adapter for role aggregate."""

from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from access.adapters.persistence.records import (
    AccessRolePermissionRecord,
    AccessRoleRecord,
    AccessScopeRecord,
)
from access.domain.actions import Action, Permission
from access.domain.roles import Role


class RoleRepositoryAdapter:
    """Resolves and persists roles against access_roles and related tables."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, role_id: str) -> Role | None:
        row = self._session.execute(
            select(AccessRoleRecord).where(
                AccessRoleRecord.role_id == UUID(role_id)
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def find_by_code(self, role_code: str) -> Role | None:
        row = self._session.execute(
            select(AccessRoleRecord).where(
                AccessRoleRecord.role_code == role_code
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def find_system_administrator_role(self) -> Role | None:
        row = self._session.execute(
            select(AccessRoleRecord).where(
                AccessRoleRecord.is_system_administrator.is_(True)
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[Role]:
        stmt = select(AccessRoleRecord).order_by(AccessRoleRecord.created_at).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        rows = self._session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in rows]

    def count(self) -> int:
        return self._session.execute(
            select(func.count()).select_from(AccessRoleRecord)
        ).scalar() or 0

    def save(self, role: Role) -> None:
        """Persist a new or updated role."""
        existing = self._session.execute(
            select(AccessRoleRecord).where(
                AccessRoleRecord.role_id == UUID(role.role_id)
            )
        ).scalar_one_or_none()

        if existing is None:
            record = AccessRoleRecord(
                role_id=UUID(role.role_id),
                role_code=role.role_code,
                role_name=role.role_name,
                description=role.description,
                is_system_administrator=role.is_system_administrator,
                is_active=role.is_active,
                version=role.version,
            )
            if role.created_at is not None:
                record.created_at = role.created_at
            if role.updated_at is not None:
                record.updated_at = role.updated_at
            self._session.add(record)
            self._session.flush()

            for perm in role.permissions:
                scope_row = self._session.execute(
                    select(AccessScopeRecord.scope_id).where(
                        AccessScopeRecord.scope_code == perm.scope_code
                    )
                ).scalar_one_or_none()
                if scope_row:
                    perm_record = AccessRolePermissionRecord(
                        role_permission_id=uuid4(),
                        role_id=UUID(role.role_id),
                        scope_id=scope_row,
                        action=perm.action,
                        created_by_user_id=UUID(role.role_id),  # placeholder
                    )
                    if role.created_at is not None:
                        perm_record.created_at = role.created_at
                    self._session.add(perm_record)
        else:
            existing.role_name = role.role_name
            existing.description = role.description
            existing.is_active = role.is_active
            existing.version = role.version
            if role.updated_at is not None:
                existing.updated_at = role.updated_at

    def _to_domain(self, row: AccessRoleRecord) -> Role:
        perm_rows = self._session.execute(
            select(AccessRolePermissionRecord).where(
                AccessRolePermissionRecord.role_id == row.role_id
            )
        ).scalars().all()

        scope_ids = {p.scope_id for p in perm_rows}
        scope_map: dict[UUID, str] = {}
        if scope_ids:
            scope_rows = self._session.execute(
                select(AccessScopeRecord.scope_id, AccessScopeRecord.scope_code).where(
                    AccessScopeRecord.scope_id.in_(scope_ids)
                )
            ).all()
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
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
