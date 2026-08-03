"""Use case: get a single authentication account by ID."""

from auth.application.dto import AccountSummary
from auth.domain.errors import AccountNotFound
from auth.ports.account_repository import AccountRepository


class GetAccount:
    """Return a non-secret account summary for administrative detail view."""

    def __init__(self, account_repository: AccountRepository) -> None:
        self._accounts = account_repository

    def execute(self, account_id: str) -> AccountSummary:
        account = self._accounts.find_by_id(account_id)
        if account is None:
            raise AccountNotFound(account_id)
        return AccountSummary(
            account_id=account.account_id,
            email=account.normalized_email.value,
            display_name=account.display_name,
            user_code=account.user_code,
            status=account.status.value,
            version=account.version,
        )
