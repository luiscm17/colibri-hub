"""Repository adapter for access change audit evidence."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from access.adapters.persistence.records import AccessChangeAuditRecord
from access.domain.audit import AccessAuditEntry


class AccessAuditRepositoryAdapter:
    """Appends and queries access_change_audits (append-only)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def append(
        self,
        *,
        operation_id: str,
        change_kind: str,
        subject_type: str,
        subject_id: str,
        performed_by_user_id: str | None,
        reason: str | None,
        before_values: dict,
        after_values: dict,
    ) -> None:
        self._session.add(AccessChangeAuditRecord(
            access_change_audit_id=uuid4(),
            operation_id=UUID(operation_id),
            change_kind=change_kind,
            subject_type=subject_type,
            subject_id=UUID(subject_id),
            performed_by_user_id=UUID(performed_by_user_id) if performed_by_user_id else None,
            reason=reason,
            before_values=before_values,
            after_values=after_values,
        ))

    def list_recent(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        subject_type: str | None = None,
        change_kind: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[AccessAuditEntry]:
        stmt = select(AccessChangeAuditRecord).order_by(
            AccessChangeAuditRecord.occurred_at.desc()
        )
        stmt = self._apply_filters(stmt, subject_type, change_kind, date_from, date_to)
        stmt = stmt.offset(offset).limit(limit)
        rows = self._session.execute(stmt).scalars().all()
        return [
            AccessAuditEntry(
                audit_id=str(r.access_change_audit_id),
                operation_id=str(r.operation_id),
                change_kind=r.change_kind,
                subject_type=r.subject_type,
                subject_id=str(r.subject_id),
                performed_by_user_id=str(r.performed_by_user_id) if r.performed_by_user_id else None,
                reason=r.reason,
                occurred_at=r.occurred_at,
            )
            for r in rows
        ]

    def count(
        self,
        *,
        subject_type: str | None = None,
        change_kind: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(AccessChangeAuditRecord)
        stmt = self._apply_filters(stmt, subject_type, change_kind, date_from, date_to)
        return self._session.execute(stmt).scalar() or 0

    @staticmethod
    def _apply_filters(stmt, subject_type, change_kind, date_from, date_to):
        if subject_type:
            stmt = stmt.where(AccessChangeAuditRecord.subject_type == subject_type)
        if change_kind:
            stmt = stmt.where(AccessChangeAuditRecord.change_kind == change_kind)
        if date_from:
            stmt = stmt.where(
                AccessChangeAuditRecord.occurred_at >= datetime.fromisoformat(date_from)
            )
        if date_to:
            stmt = stmt.where(
                AccessChangeAuditRecord.occurred_at <= datetime.fromisoformat(date_to)
            )
        return stmt
