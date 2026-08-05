"""Use case: query access-change audit history with pagination and filters."""

from dataclasses import dataclass

from access.application.results import AuditEntryResult
from access.ports.audit import AccessAuditRepository


@dataclass(frozen=True, slots=True)
class PaginatedAudits:
    items: list[AuditEntryResult]
    total: int


class ListAccessAudits:
    def __init__(self, *, audit_repository: AccessAuditRepository) -> None:
        self._audits = audit_repository

    def execute(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        subject_type: str | None = None,
        change_kind: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> PaginatedAudits:
        offset = (page - 1) * page_size
        entries = self._audits.list_recent(
            limit=page_size,
            offset=offset,
            subject_type=subject_type,
            change_kind=change_kind,
            date_from=date_from,
            date_to=date_to,
        )
        total = self._audits.count(
            subject_type=subject_type,
            change_kind=change_kind,
            date_from=date_from,
            date_to=date_to,
        )
        return PaginatedAudits(
            items=[
                AuditEntryResult(
                    audit_id=e.audit_id,
                    operation_id=e.operation_id,
                    change_kind=e.change_kind,
                    subject_type=e.subject_type,
                    subject_id=e.subject_id,
                    performed_by_user_id=e.performed_by_user_id,
                    reason=e.reason,
                    occurred_at=e.occurred_at.isoformat() if e.occurred_at else "",
                )
                for e in entries
            ],
            total=total,
        )
