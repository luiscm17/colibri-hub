"""Use case: list all access user profiles."""

from access.application.results import AccessUserResult
from access.ports.users import AccessUserRepository


class ListAccessUsers:
    def __init__(self, *, user_repository: AccessUserRepository) -> None:
        self._users = user_repository

    def execute(self) -> list[AccessUserResult]:
        users = self._users.list_all()
        return [
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
        ]
