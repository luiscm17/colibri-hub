"""Use case: list authentication accounts."""

from auth.application.results import AccountSummary
from auth.ports.account_repository import AuthAccountRepository


class ListAccounts:
    """Return all accounts as non-secret summaries."""

    def __init__(self, account_repository: AuthAccountRepository) -> None:
        self._accounts = account_repository

    def execute(self) -> list[AccountSummary]:
        accounts = self._accounts.list_all()
        return [
            AccountSummary(
                account_id=a.account_id,
                email=a.normalized_email.value,
                display_name=a.display_name,
                user_code=a.user_code,
                status=a.status.value,
                version=a.version,
            )
            for a in accounts
        ]
