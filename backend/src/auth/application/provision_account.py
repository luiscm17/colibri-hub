"""Use case: unified provisioning of account and Access profile."""

from auth.application.results import AccountSummary
from auth.application.commands import ProvisionAccountCommand
from auth.domain.account import AuthenticationAccount
from auth.domain.email import NormalizedEmail
from auth.domain.errors import (
    DuplicateEmail,
    ProviderUnavailable,
)
from auth.ports.account_repository import AuthAccountRepository
from auth.ports.access_provisioning import AccessProvisioningPort
from auth.ports.audit_repository import AuthAuditEntry, AuthAuditRepository
from auth.ports.clock import ClockPort
from auth.ports.identity import IdentityPort
from auth.ports.identity_provider import IdentityProviderPort


class ProvisionAccount:
    """Create provider identity, auth account, Access profile, and initial roles.

    Safe orchestration per tech spec §10:
    1. Create provider identity (without email)
    2. In one transaction: create auth account + Access profile + roles + audits
    3. On app failure: compensate by removing the never-established provider identity
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

    def execute(self, command: ProvisionAccountCommand) -> AccountSummary:
        email = NormalizedEmail.from_raw(command.email)
        operation_id = self._identity.generate_operation_id()

        # Validate uniqueness in the application store
        existing = self._accounts.find_by_email(email)
        if existing is not None:
            raise DuplicateEmail()

        # Create provider identity (no email sent)
        provider_identity = self._provider.create_user(
            email=email.value,
            password=command.provisional_password,
        )

        # Application persistence (safe ordering: provider identity exists
        # but is unusable until app persistence succeeds)
        try:
            now = self._clock.now()
            account = AuthenticationAccount.provision(
                account_id=self._identity.generate_id(),
                identity_subject=provider_identity.subject,
                email=email,
                display_name=command.display_name,
                user_code=command.user_code,
                now=now,
            )
            self._accounts.save(account)

            # Coordinate Access Control profile and initial roles
            self._access.provision_profile(
                subject=provider_identity.subject,
                profile_code=command.user_code,
                role_codes=command.role_codes,
                actor_subject=command.actor_subject,
                reason=command.reason,
                operation_id=operation_id,
            )

            self._audits.append(
                AuthAuditEntry(
                    audit_id=self._identity.generate_id(),
                    operation_id=operation_id,
                    event_type="account_provisioned",
                    outcome="succeeded",
                    actor_identity_subject=command.actor_subject,
                    affected_account_id=account.account_id,
                    provider_session_id=None,
                    reason=command.reason,
                    details={
                        "email": email.value,
                        "user_code": command.user_code,
                        "role_codes": command.role_codes,
                    },
                    occurred_at=now.isoformat(),
                )
            )
        except Exception:
            # Compensation: remove never-established provider identity
            try:
                self._provider.delete_user(subject=provider_identity.subject)
            except Exception:
                pass  # Quarantined — identity has no app account, no access
            raise

        return AccountSummary(
            account_id=account.account_id,
            email=account.normalized_email.value,
            display_name=account.display_name,
            user_code=account.user_code,
            status=account.status.value,
            version=account.version,
        )
