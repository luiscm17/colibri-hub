"""Use case: administrative password reset."""

from auth.application.commands import ResetPasswordCommand
from auth.domain.errors import (
    AccountNotFound,
    LastSystemAdministratorRequired,
    VersionConflict,
)
from auth.ports.access_provisioning import AccessProvisioningPort
from auth.ports.account_repository import AuthAccountRepository
from auth.ports.audit_repository import AuthAuditEntry, AuthAuditRepository
from auth.ports.clock import ClockPort
from auth.ports.identity import IdentityPort
from auth.ports.identity_provider import IdentityProviderPort
from auth.ports.transaction import Transaction


class ResetPassword:
    """Set a new provisional password, revoke sessions, require replacement.

    Safe ordering: establish account denial BEFORE provider credential
    replacement and revocation.
    """

    def __init__(
        self,
        *,
        account_repository: AuthAccountRepository,
        audit_repository: AuthAuditRepository,
        identity_provider: IdentityProviderPort,
        access_provisioning: AccessProvisioningPort,
        transaction: Transaction,
        clock: ClockPort,
        identity: IdentityPort,
    ) -> None:
        self._accounts = account_repository
        self._audits = audit_repository
        self._provider = identity_provider
        self._access = access_provisioning
        self._transaction = transaction
        self._clock = clock
        self._identity = identity

    def execute(self, command: ResetPasswordCommand) -> None:
        account = self._accounts.find_by_id(command.account_id)
        if account is None:
            raise AccountNotFound(command.account_id)

        if not account.check_version(command.expected_version):
            raise VersionConflict()

        # Last-admin check before any state change
        if self._access.would_remove_last_administrator(account.identity_subject):
            raise LastSystemAdministratorRequired()

        # Establish account denial first (safe ordering)
        now = self._clock.now()
        account.reset_to_awaiting(now)
        self._accounts.save(account)
        self._transaction.commit()

        # Provider operations after account denial is persisted
        self._provider.update_password(
            subject=account.identity_subject,
            new_password=command.provisional_password,
        )
        self._provider.revoke_subject_sessions(subject=account.identity_subject)

        operation_id = self._identity.generate_operation_id()
        self._audits.append(
            AuthAuditEntry(
                audit_id=self._identity.generate_id(),
                operation_id=operation_id,
                event_type="password_reset",
                outcome="succeeded",
                actor_identity_subject=command.actor_subject,
                affected_account_id=account.account_id,
                provider_session_id=None,
                reason=command.reason,
                details={"transition": "active -> awaiting_password_change"},
                occurred_at=now.isoformat(),
            )
        )
