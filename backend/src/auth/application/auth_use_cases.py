"""Typed containers for composed auth use case dependencies."""

from collections.abc import Callable
from dataclasses import dataclass

from auth.application.change_required_password import ChangeRequiredPassword
from auth.application.disable_account import DisableAccount
from auth.application.enable_account import EnableAccount
from auth.application.get_account import GetAccount
from auth.application.get_current_authentication import GetCurrentAuthentication
from auth.application.list_accounts import ListAccounts
from auth.application.list_audits import ListAudits
from auth.application.provision_account import ProvisionAccount
from auth.application.record_logout import RecordLogout
from auth.application.reset_password import ResetPassword


@dataclass(frozen=True, slots=True)
class AuthUseCases:
    """Typed container for authentication use case dependencies.

    Replaces the stringly-typed dict that was returned by the bootstrap
    dependency factory, providing attribute access with full type safety.
    """

    get_current_authentication: GetCurrentAuthentication
    change_required_password: ChangeRequiredPassword
    record_logout: RecordLogout
    provision_account: ProvisionAccount
    reset_password: ResetPassword
    disable_account: DisableAccount
    enable_account: EnableAccount
    get_account: GetAccount
    list_accounts: ListAccounts
    list_audits: ListAudits


AuthUseCaseProvider = Callable[..., AuthUseCases]
"""Dependency that builds an AuthUseCases container per request."""
