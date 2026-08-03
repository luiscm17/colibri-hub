from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Protocol

from access.domain.models import AccessProfile, Role, RoleAssignment, Scope


@dataclass(slots=True)
class AccessState:
    bootstrap_operation_id: str | None = None
    profiles: list[AccessProfile] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)
    scopes: list[Scope] = field(default_factory=list)
    assignments: list[RoleAssignment] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AuditCommand:
    actor_subject: str | None
    affected_subject: str
    change_kind: str
    reason: str | None
    operation_id: str
    before: dict[str, object]
    after: dict[str, object]


class AccessStore(Protocol):
    def serialized(self) -> AbstractContextManager[None]: ...
    def load(self) -> AccessState: ...
    def commit(self, state: AccessState, audit: AuditCommand) -> None: ...
