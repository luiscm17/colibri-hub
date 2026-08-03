"""Use case: inspect the current authentication state for a verified identity."""

from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.errors import AccountNotFound
from auth.application.dto import CurrentAuthenticationResult
from auth.ports.account_repository import AccountRepository


class GetCurrentAuthentication:
    """Return account state and required next step for a verified provider identity."""

    def __init__(self, account_repository: AccountRepository) -> None:
        self._accounts = account_repository

    def execute(self, identity_subject: str) -> CurrentAuthenticationResult:
        account = self._accounts.find_by_subject(identity_subject)
        if account is None:
            raise AccountNotFound(identity_subject)

        next_step = (
            "change_password"
            if account.status == AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE
            else "load_access"
        )

        return CurrentAuthenticationResult(
            account_id=account.account_id,
            email=account.normalized_email.value,
            display_name=account.display_name,
            status=account.status.value,
            next_step=next_step,
        )
