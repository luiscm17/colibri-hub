"""Use case: list access user profiles with pagination."""

from dataclasses import dataclass

from access.application.results import AccessUserResult
from access.ports.users import AccessUserRepository


@dataclass(frozen=True, slots=True)
class PaginatedUsers:
    items: list[AccessUserResult]
    total: int


class ListAccessUsers:
    def __init__(self, *, user_repository: AccessUserRepository) -> None:
        self._users = user_repository

    def execute(
        self, *, page: int = 1, page_size: int = 50
    ) -> PaginatedUsers:
        offset = (page - 1) * page_size
        users = self._users.list_all(limit=page_size, offset=offset)
        total = self._users.count()
        return PaginatedUsers(
            items=[
                AccessUserResult(
                    user_id=u.user_id,
                    identity_subject=u.identity_subject,
                    user_code=u.user_code,
                    display_name=u.display_name,
                    is_active=u.is_active,
                    authorization_version=u.authorization_version,
                    version=u.version,
                )
                for u in users
            ],
            total=total,
        )
