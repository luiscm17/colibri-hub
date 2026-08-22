"""Use case: mandatory replacement of a provisional password."""

from auth.application.commands import ChangePasswordCommand
from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.errors import (
    AccountNotFound,
    AccountStateConflict,
    ProviderUnavailable,
    ReplacementPasswordMustDiffer,
)
from auth.ports.account_repository import AuthAccountRepository
from auth.ports.audit_repository import AuthAuditEntry, AuthAuditRepository
from auth.ports.clock import ClockPort
from auth.ports.identity import IdentityPort
from auth.ports.password_replacement import PasswordReplacementPort


class ChangeRequiredPassword:
    """Replace a provisional password, activate the account.

    Does not restart, extend, rotate, or substitute the provider session.
    """

    def __init__(
        self,
        *,
        account_repository: AuthAccountRepository,
        audit_repository: AuthAuditRepository,
        password_replacement: PasswordReplacementPort | None = None,
        clock: ClockPort,
        identity: IdentityPort,
    ) -> None:
        self._accounts = account_repository
        self._audits = audit_repository
        self._password_replacement = password_replacement
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

        if self._password_replacement is None:
            raise ProviderUnavailable()

        # Replacement is provider-first: every failure leaves the account in
        # awaiting state. No administrative or recovery fallback is attempted.
        self._password_replacement.replace_required_password(
            subject=command.actor_subject,
            session_id=command.session_id,
            current_password=command.current_password,
            new_password=command.new_password,
        )

        # Activate the account only after provider success
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
