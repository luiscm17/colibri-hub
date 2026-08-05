"""Repository adapter for user-role assignment lifecycle."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from access.adapters.persistence.records import AccessUserRoleAssignmentRecord
from access.domain.roles import Assignment


class AssignmentRepositoryAdapter:
    """Persists and queries user-role assignments independently of roles."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_for_user(self, user_id: str) -> list[Assignment]:
        rows = self._session.execute(
            select(AccessUserRoleAssignmentRecord).where(
                AccessUserRoleAssignmentRecord.user_id == UUID(user_id),
                AccessUserRoleAssignmentRecord.revoked_at.is_(None),
            )
        ).scalars().all()
        return [self._to_assignment(r) for r in rows]

    def find_for_role(self, role_id: str) -> list[Assignment]:
        rows = self._session.execute(
            select(AccessUserRoleAssignmentRecord).where(
                AccessUserRoleAssignmentRecord.role_id == UUID(role_id),
                AccessUserRoleAssignmentRecord.revoked_at.is_(None),
            )
        ).scalars().all()
        return [self._to_assignment(r) for r in rows]

    def save(self, assignment: Assignment) -> None:
        """Persist a new or updated assignment."""
        existing = self._session.execute(
            select(AccessUserRoleAssignmentRecord).where(
                AccessUserRoleAssignmentRecord.assignment_id == UUID(assignment.assignment_id)
            )
        ).scalar_one_or_none()

        if existing is None:
            self._session.add(AccessUserRoleAssignmentRecord(
                assignment_id=UUID(assignment.assignment_id),
                user_id=UUID(assignment.user_id),
                role_id=UUID(assignment.role_id),
                assigned_by_user_id=UUID(assignment.assigned_by_user_id),
                assigned_at=assignment.assigned_at,
                revoked_by_user_id=UUID(assignment.revoked_by_user_id) if assignment.revoked_by_user_id else None,
                revoked_at=assignment.revoked_at,
                revoke_reason=assignment.revoke_reason,
            ))
        else:
            existing.revoked_by_user_id = UUID(assignment.revoked_by_user_id) if assignment.revoked_by_user_id else None
            existing.revoked_at = assignment.revoked_at
            existing.revoke_reason = assignment.revoke_reason

    @staticmethod
    def _to_assignment(row: AccessUserRoleAssignmentRecord) -> Assignment:
        return Assignment(
            assignment_id=str(row.assignment_id),
            user_id=str(row.user_id),
            role_id=str(row.role_id),
            assigned_by_user_id=str(row.assigned_by_user_id),
            assigned_at=row.assigned_at,
            revoked_by_user_id=str(row.revoked_by_user_id) if row.revoked_by_user_id else None,
            revoked_at=row.revoked_at,
            revoke_reason=row.revoke_reason,
        )
