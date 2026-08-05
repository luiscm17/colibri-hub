"""Domain read model for access-change audit entries."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AccessAuditEntry:
    """Typed representation of an immutable access-change audit record.

    Used by ports to return structured audit data without coupling
    the domain to persistence or application DTOs.
    """

    audit_id: str
    operation_id: str
    change_kind: str
    subject_type: str
    subject_id: str
    performed_by_user_id: str | None
    reason: str | None
    occurred_at: datetime
