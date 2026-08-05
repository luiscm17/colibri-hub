"""Use case: disable an authentication account."""

from auth.application.commands import DisableAccountCommand
from auth.domain.errors import (
    AccountNotFound,
    LastSystemAdministratorRequired,
    VersionConflict,
)
from auth.ports.account_repository import AuthAccountRepository
from auth.ports.access_provisioning import AccessProvisioningPort
from auth.ports.audit_repository import AuthAuditEntry, AuthAuditRepository
from auth.ports.clock import ClockPort
from auth.ports.identity import IdentityPort
from auth.ports.identity_provider import IdentityProviderPort


class DisableAccount:
    """Establish local denial, deactivate Access profile, ban provider, revoke sessions.

    Safe ordering: local + Access denial BEFORE provider ban and revocation.
    """

    def __init__(
        self,
        *,
        account_repository: AuthAccountRepository,
        audit_repository: AuthAuditRepository,
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

    def execute(self, command: DisableAccountCommand) -> None:
        account = self._accounts.find_by_id(command.account_id)
        if account is None:
            raise AccountNotFound(command.account_id)

        if not account.check_version(command.expected_version):
            raise VersionConflict()

        # Last-admin check
        if self._access.would_remove_last_administrator(account.identity_subject):
            raise LastSystemAdministratorRequired()

        now = self._clock.now()
        operation_id = self._identity.generate_operation_id()

        # Local denial first
        account.disable(now)
        self._accounts.save(account)

        # Deactivate Access profile
        self._access.deactivate_profile(
            subject=account.identity_subject,
            actor_subject=command.actor_subject,
            reason=command.reason,
            operation_id=operation_id,
        )

        # Provider ban and session revocation
        self._provider.ban_user(subject=account.identity_subject)
        self._provider.revoke_sessions(subject=account.identity_subject)

        self._audits.append(
            AuthAuditEntry(
                audit_id=self._identity.generate_id(),
                operation_id=operation_id,
                event_type="account_disabled",
                outcome="succeeded",
                actor_identity_subject=command.actor_subject,
                affected_account_id=account.account_id,
                provider_session_id=None,
                reason=command.reason,
                details={"previous_status": "active"},
                occurred_at=now.isoformat(),
            )
        )
