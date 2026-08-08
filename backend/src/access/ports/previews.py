"""Read-only query contract for access-change impact previews."""

from dataclasses import dataclass
from typing import Protocol

from access.domain.actions import Permission


@dataclass(frozen=True, slots=True)
class PreviewUser:
    user_id: str
    user_code: str
    display_name: str


@dataclass(frozen=True, slots=True)
class PreviewRole:
    role_id: str
    role_code: str
    role_name: str


@dataclass(frozen=True, slots=True)
class PreviewResult:
    subject_version: int
    affected_users: list[PreviewUser]
    permissions_added: frozenset[Permission]
    permissions_removed: frozenset[Permission]
    roles_added: list[PreviewRole]
    roles_removed: list[PreviewRole]


class RolePreviewQuery(Protocol):
    """Calculate preview data without taking locks or writing state."""

    def preview_role_change(self, role_id: str, proposed: set[Permission]) -> PreviewResult: ...

    def preview_user_role_replacement(self, user_id: str, role_ids: list[str]) -> PreviewResult: ...
