"""Repository adapter for access user aggregate."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from access.adapters.persistence.records import (
    AccessRoleRecord,
    AccessUserRecord,
    AccessUserRoleAssignmentRecord,
)
from access.domain.users import AccessUser


class AccessUserRepositoryAdapter:
    """Resolves and persists access users against access_users table."""

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
            select(AccessUserRecord).where(
                AccessUserRecord.user_id == UUID(user_id)
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[AccessUser]:
        stmt = select(AccessUserRecord).order_by(AccessUserRecord.created_at).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        rows = self._session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in rows]

    def count(self) -> int:
        return self._session.execute(
            select(func.count()).select_from(AccessUserRecord)
        ).scalar() or 0

    def save(self, user: AccessUser) -> None:
        existing = self._session.execute(
            select(AccessUserRecord).where(
                AccessUserRecord.user_id == UUID(user.user_id)
            )
        ).scalar_one_or_none()

        if existing is None:
            record = AccessUserRecord(
                user_id=UUID(user.user_id),
                identity_subject=user.identity_subject,
                user_code=user.user_code,
                display_name=user.display_name,
                is_active=user.is_active,
                authorization_version=user.authorization_version,
                version=user.version,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            self._session.add(record)
        else:
            existing.display_name = user.display_name
            existing.is_active = user.is_active
            existing.authorization_version = user.authorization_version
            existing.version = user.version
            existing.updated_at = user.updated_at

    def count_active_administrators(
        self, *, exclude_user_id: str | None = None, for_update: bool = False
    ) -> int:
        admin_role = self._session.execute(
            select(AccessRoleRecord.role_id).where(
                AccessRoleRecord.is_system_administrator.is_(True)
            )
        ).scalar_one_or_none()

        if admin_role is None:
            return 0

        stmt = (
            select(func.count())
            .select_from(AccessUserRoleAssignmentRecord)
            .join(
                AccessUserRecord,
                AccessUserRoleAssignmentRecord.user_id == AccessUserRecord.user_id,
            )
            .where(
                AccessUserRoleAssignmentRecord.role_id == admin_role,
                AccessUserRoleAssignmentRecord.revoked_at.is_(None),
                AccessUserRecord.is_active.is_(True),
            )
        )

        if exclude_user_id:
            stmt = stmt.where(AccessUserRecord.user_id != UUID(exclude_user_id))

        if for_update:
            stmt = stmt.with_for_update()

        return self._session.execute(stmt).scalar() or 0

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
