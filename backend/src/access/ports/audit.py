"""Repository protocol for access change audit evidence."""

from typing import Protocol

from access.domain.audit import AccessAuditEntry


class AccessAuditRepository(Protocol):
    """Append immutable access-change audit evidence."""

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
        """Record one audit entry. Append-only — updates and deletes are forbidden."""
        ...

    def list_recent(self, *, limit: int = 50) -> list[AccessAuditEntry]:
        """Return recent audit entries ordered by occurred_at descending."""
        ...
