"""Use case: query paginated authentication audit evidence."""

from auth.ports.audit_repository import AuthAuditEntry, AuthAuditRepository


class ListAudits:
    """Return paginated, redacted authentication audit evidence."""

    def __init__(self, audit_repository: AuthAuditRepository) -> None:
        self._audits = audit_repository

    def execute(self, *, limit: int = 50) -> list[AuthAuditEntry]:
        return self._audits.list_recent(limit=limit)
