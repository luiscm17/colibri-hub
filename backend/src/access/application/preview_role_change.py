"""Use case: preview a shared role configuration change."""

from access.domain.actions import Permission
from access.ports.previews import PreviewResult, RolePreviewQuery


class PreviewRoleChange:
    def __init__(self, *, preview_query: RolePreviewQuery) -> None:
        self._query = preview_query

    def execute(self, *, role_id: str, permissions: set[Permission]) -> PreviewResult:
        return self._query.preview_role_change(role_id, permissions)
