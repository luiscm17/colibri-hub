"""Use case: query access-change audit history."""

from access.application.results import AuditEntryResult
from access.ports.audit import AccessAuditRepository


class ListAccessAudits:
    def __init__(self, *, audit_repository: AccessAuditRepository) -> None:
        self._audits = audit_repository

    def execute(self, *, limit: int = 50) -> list[AuditEntryResult]:
        entries = self._audits.list_recent(limit=limit)
        return [
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
        ]
