"""Use case: mandatory replacement of a provisional password."""

from auth.application.commands import ChangePasswordCommand
from auth.domain.errors import (
    AccountNotFound,
    AccountStateConflict,
    PasswordChangeRequired,
    ReplacementPasswordMustDiffer,
)
from auth.domain.account_status import AuthenticationAccountStatus
from auth.ports.account_repository import AuthAccountRepository
from auth.ports.audit_repository import AuthAuditEntry, AuthAuditRepository
from auth.ports.clock import ClockPort
from auth.ports.identity import IdentityPort
from auth.ports.identity_provider import IdentityProviderPort


class ChangeRequiredPassword:
    """Replace a provisional password, activate the account.

    Does NOT restart or extend the provider session's eight-hour maximum.
    """

    def __init__(
        self,
        *,
        account_repository: AuthAccountRepository,
        audit_repository: AuthAuditRepository,
        identity_provider: IdentityProviderPort,
        clock: ClockPort,
        identity: IdentityPort,
    ) -> None:
        self._accounts = account_repository
        self._audits = audit_repository
        self._provider = identity_provider
        self._clock = clock
        self._identity = identity

    def execute(self, command: ChangePasswordCommand) -> None:
        account = self._accounts.find_by_subject(command.actor_subject)
        if account is None:
            raise AccountNotFound(command.actor_subject)

        if account.status != AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE:
            raise AccountStateConflict(account.status.value, "change_password")

        if command.current_password == command.new_password:
            raise ReplacementPasswordMustDiffer()

        # Update credential in the provider first (safe ordering: provider
        # failure leaves account in awaiting state, which is the safe default)
        self._provider.update_password(
            subject=command.actor_subject,
            new_password=command.new_password,
        )

        # Activate locally only after provider success
        now = self._clock.now()
        account.activate(now)
        self._accounts.save(account)

        self._audits.append(
            AuthAuditEntry(
                audit_id=self._identity.generate_id(),
                operation_id=self._identity.generate_operation_id(),
                event_type="password_changed",
                outcome="succeeded",
                actor_identity_subject=command.actor_subject,
                affected_account_id=account.account_id,
                provider_session_id=command.session_id,
                reason=None,
                details={"transition": "awaiting_password_change -> active"},
                occurred_at=now.isoformat(),
            )
        )
