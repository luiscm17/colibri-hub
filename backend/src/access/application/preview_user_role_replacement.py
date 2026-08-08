"""Use case: preview a user's complete role replacement."""

from access.ports.previews import PreviewResult, RolePreviewQuery


class PreviewUserRoleReplacement:
    def __init__(self, *, preview_query: RolePreviewQuery) -> None:
        self._query = preview_query

    def execute(self, *, user_id: str, role_ids: list[str]) -> PreviewResult:
        return self._query.preview_user_role_replacement(user_id, role_ids)
