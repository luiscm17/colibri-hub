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
        """Return audit entries ordered by occurred_at descending with filters."""
        ...

    def count(
        self,
        *,
        subject_type: str | None = None,
        change_kind: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> int:
        """Return total count of audit entries matching the given filters."""
        ...
