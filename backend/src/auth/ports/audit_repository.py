"""Port for authentication audit persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
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
    details: dict[str, object] = field(default_factory=dict)
    occurred_at: str | None = None


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
