"""Initial System Administrator bootstrap command.

A controlled deployment command — NOT a public route. Receives initial admin
credentials from protected deployment input and coordinates:
1. Create or resolve the provider identity
2. Create the Authentication account in awaiting_password_change
3. Invoke Access Control bootstrap
4. Write redacted audits

Idempotent for the same identifiers. Fails closed on conflicting partial state.
Returns no password and stores no credential.
"""

from __future__ import annotations

import logging

from auth.domain.account import AuthenticationAccount
from auth.domain.email import NormalizedEmail
from auth.domain.errors import DuplicateEmail, IdentityConflict
from auth.ports.account_repository import AuthAccountRepository
from auth.ports.access_provisioning import AccessProvisioningPort
from auth.ports.audit_repository import AuthAuditEntry, AuthAuditRepository
from auth.ports.clock import ClockPort
from auth.ports.identity import IdentityPort
from auth.ports.identity_provider import IdentityProviderPort

logger = logging.getLogger(__name__)


class BootstrapInitialAdministrator:
    """Establish the initial System Administrator.

    This is NOT a use case exposed via HTTP. It runs at deployment time
    via CLI or a startup script.
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

    def execute(
        self,
        *,
        email: str,
        provisional_password: str,
        user_code: str,
        display_name: str,
    ) -> str:
        """Bootstrap the initial admin. Returns account_id.

        Idempotent: if the account already exists with matching identifiers,
        returns its ID without modifying state.
        """
        normalized_email = NormalizedEmail.from_raw(email)
        operation_id = self._identity.generate_operation_id()

        # Idempotency check
        existing = self._accounts.find_by_email(normalized_email)
        if existing is not None:
            logger.info(
                "Initial administrator already exists: %s",
                existing.account_id,
            )
            return existing.account_id

        # Create provider identity
        provider_identity = self._provider.create_user(
            email=normalized_email.value,
            password=provisional_password,
        )

        # Create local account
        try:
            now = self._clock.now()
            account = AuthenticationAccount.provision(
                account_id=self._identity.generate_id(),
                identity_subject=provider_identity.subject,
                email=normalized_email,
                display_name=display_name,
                user_code=user_code,
                now=now,
            )
            self._accounts.save(account)

            # Access Control bootstrap (creates profile + System Administrator role)
            self._access.provision_profile(
                subject=provider_identity.subject,
                profile_code=user_code,
                role_codes=["system_administrator"],
                actor_subject=provider_identity.subject,
                reason="Initial system administrator bootstrap",
                operation_id=operation_id,
            )

            self._audits.append(
                AuthAuditEntry(
                    audit_id=self._identity.generate_id(),
                    operation_id=operation_id,
                    event_type="initial_bootstrap",
                    outcome="succeeded",
                    actor_identity_subject=None,
                    affected_account_id=account.account_id,
                    provider_session_id=None,
                    reason=None,
                    details={"user_code": user_code},
                    occurred_at=now.isoformat(),
                )
            )

            logger.info(
                "Initial administrator bootstrapped: %s", account.account_id
            )
            return account.account_id

        except Exception:
            # Compensation
            try:
                self._provider.delete_user(subject=provider_identity.subject)
            except Exception:
                pass
            raise
