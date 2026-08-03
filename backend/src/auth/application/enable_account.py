"""Use case: re-enable a disabled authentication account."""

from auth.application.dto import EnableAccountCommand
from auth.domain.errors import (
    AccountNotFound,
    VersionConflict,
)
from auth.ports.account_repository import AccountRepository
from auth.ports.access_provisioning import AccessProvisioningPort
from auth.ports.audit_repository import AuditEntry, AuditRepository
from auth.ports.clock import ClockPort
from auth.ports.identity import IdentityPort
from auth.ports.identity_provider import IdentityProviderPort


class EnableAccount:
    """Set a new provisional password, validate Access, unban provider, enable locally.

    Safe ordering: keep local denial until provider update and Access validation succeed.
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

    def execute(self, command: EnableAccountCommand) -> None:
        account = self._accounts.find_by_id(command.account_id)
        if account is None:
            raise AccountNotFound(command.account_id)

        if not account.check_version(command.expected_version):
            raise VersionConflict()

        now = self._clock.now()
        operation_id = self._identity.generate_operation_id()

        # Update provider credential and unban BEFORE local state change
        # (if provider fails, account stays disabled — safe)
        self._provider.update_password(
            subject=account.identity_subject,
            new_password=command.provisional_password,
        )
        self._provider.unban_user(subject=account.identity_subject)

        # Reactivate Access profile
        self._access.activate_profile(
            subject=account.identity_subject,
            actor_subject=command.actor_subject,
            reason=command.reason,
            operation_id=operation_id,
        )

        # Local state change last (after provider and Access success)
        account.enable(now)
        self._accounts.save(account)

        self._audits.append(
            AuditEntry(
                audit_id=self._identity.generate_id(),
                operation_id=operation_id,
                event_type="account_enabled",
                outcome="succeeded",
                actor_identity_subject=command.actor_subject,
                affected_account_id=account.account_id,
                provider_session_id=None,
                reason=command.reason,
                details={"transition": "disabled -> awaiting_password_change"},
                occurred_at=now.isoformat(),
            )
        )
