"""Use case: query access-change audit history."""

from access.application.dto import AuditEntryResult
from access.ports.repositories import AccessAuditRepository


class ListAccessAudits:
    def __init__(self, *, audit_repository: AccessAuditRepository) -> None:
        self._audits = audit_repository

    def execute(self, *, limit: int = 50) -> list[AuditEntryResult]:
        entries = self._audits.list_recent(limit=limit)
        return entries
