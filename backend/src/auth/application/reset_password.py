"""Use case: administrative password reset."""

from auth.application.dto import ResetPasswordCommand
from auth.domain.errors import (
    AccountNotFound,
    LastSystemAdministratorRequired,
    VersionConflict,
)
from auth.ports.account_repository import AccountRepository
from auth.ports.access_provisioning import AccessProvisioningPort
from auth.ports.audit_repository import AuditEntry, AuditRepository
from auth.ports.clock import ClockPort
from auth.ports.identity import IdentityPort
from auth.ports.identity_provider import IdentityProviderPort


class ResetPassword:
    """Set a new provisional password, revoke sessions, require replacement.

    Safe ordering: establish local denial BEFORE provider credential
    replacement and revocation.
    """

    def __init__(
        self,
        *,
        account_repository: AccountRepository,
        audit_repository: AuditRepository,
        identity_provider: IdentityProviderPort,
        access_provisioning: AccessProvisioningPort,
        clock: ClockPort,
        identity: IdentityPort,
    ) -> None:
        self._accounts = account_repository
        self._audits = audit_repository
        self._provider = identity_provider
        self._access = access_provisioning
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

        # Establish local denial first (safe ordering)
        now = self._clock.now()
        account.reset_to_awaiting(now)
        self._accounts.save(account)

        # Provider operations after local denial is persisted
        self._provider.update_password(
            subject=account.identity_subject,
            new_password=command.provisional_password,
        )
        self._provider.revoke_sessions(subject=account.identity_subject)

        operation_id = self._identity.generate_operation_id()
        self._audits.append(
            AuditEntry(
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
