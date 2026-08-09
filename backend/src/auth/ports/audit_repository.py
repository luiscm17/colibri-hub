"""Port for authentication audit persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AuthAuditEntry:
    """Redacted application-owned authentication audit entry."""

    audit_id: str
    operation_id: str
    event_type: str
    outcome: str
    actor_identity_subject: str | None
    affected_account_id: str | None
    provider_session_id: str | None
    reason: str | None
    details: dict[str, object]
    occurred_at: str
    source: str = "application"

    def __post_init__(self) -> None:
        if not self.occurred_at:
            raise ValueError("Authentication audit entries require occurred_at")


class AuthAuditRepository(Protocol):
    """Append and query redacted application-owned authentication audits."""

    def append(self, entry: AuthAuditEntry) -> None:
        """Append an immutable audit entry."""
        ...

    def list_by_account(self, account_id: str) -> list[AuthAuditEntry]:
        """Return audit entries for a specific account, ordered by time."""
        ...

    def list_recent(self, limit: int = 50) -> list[AuthAuditEntry]:
        """Return the most recent audit entries."""
        ...

    def list_keyset(self, *, as_of: str, cursor: tuple[str, str] | None, limit: int) -> list[AuthAuditEntry]:
        """Return application audits within a stable timestamp/id boundary."""
        ...
