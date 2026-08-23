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

from access.domain.errors import AccessError
from sqlalchemy.exc import SQLAlchemyError

from auth.domain.account import AuthenticationAccount
from auth.domain.email import NormalizedEmail
from auth.domain.errors import AuthenticationError, ProviderUnavailable
from auth.ports.access_provisioning import AccessProvisioningPort
from auth.ports.account_repository import AuthAccountRepository
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

        completed = False
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
                display_name=display_name,
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

            logger.info("Initial administrator bootstrapped: %s", account.account_id)
            completed = True
            return account.account_id
        finally:
            if not completed:
                try:
                    self._provider.delete_user(subject=provider_identity.subject)
                except ProviderUnavailable:
                    logger.warning(
                        "Failed to delete compensating identity %s",
                        provider_identity.subject,
                    )


def main() -> None:
    """CLI entrypoint for initial administrator bootstrap.

    Usage:
        uv run --package backend python -m auth.adapters.bootstrap_command

    Required environment variables:
        BOOTSTRAP_EMAIL — administrator email
        BOOTSTRAP_PASSWORD — provisional password (must be changed on first login)
        BOOTSTRAP_USER_CODE — unique user code (e.g. USR-001)
        BOOTSTRAP_DISPLAY_NAME — display name for the administrator
    """
    import os
    import sys

    from infra.configuration import ApplicationSettings
    from infra.persistence.database_engine import create_db_engine
    from infra.persistence.database_session_factory import create_session_factory
    from infra.persistence.record_registry import register_auth_records

    email = os.environ.get("BOOTSTRAP_EMAIL")
    password = os.environ.get("BOOTSTRAP_PASSWORD")
    user_code = os.environ.get("BOOTSTRAP_USER_CODE")
    display_name = os.environ.get("BOOTSTRAP_DISPLAY_NAME")

    missing = [
        name
        for name, val in [
            ("BOOTSTRAP_EMAIL", email),
            ("BOOTSTRAP_PASSWORD", password),
            ("BOOTSTRAP_USER_CODE", user_code),
            ("BOOTSTRAP_DISPLAY_NAME", display_name),
        ]
        if not val
    ]
    if missing:
        print(
            f"ERROR: Missing environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

    assert email and password and user_code and display_name

    # Compose dependencies
    settings = ApplicationSettings()
    engine = create_db_engine(settings.database)
    session_factory = create_session_factory(engine)
    register_auth_records()

    from access.adapters.access_provisioning import AccessProvisioningAdapter
    from access.adapters.persistence.administrator_continuity import (
        AdministratorContinuityAdapter,
    )
    from access.adapters.persistence.assignment_repository import (
        AssignmentRepositoryAdapter,
    )
    from access.adapters.persistence.audit_repository import (
        AccessAuditRepositoryAdapter,
    )
    from access.adapters.persistence.role_repository import RoleRepositoryAdapter
    from access.adapters.persistence.transaction import (
        TransactionAdapter as AccessTransactionAdapter,
    )
    from access.adapters.persistence.user_repository import AccessUserRepositoryAdapter
    from access.application.activate_access_user import ActivateAccessUser
    from access.application.create_access_user import CreateAccessUser
    from access.application.deactivate_access_user import DeactivateAccessUser
    from infra.clock import SystemClock
    from infra.identity import SystemIdentity

    from auth.adapters.identity_provider.admin_client import IdentityProviderAdapter
    from auth.adapters.persistence.account_repository import (
        AuthAccountRepositoryAdapter,
    )
    from auth.adapters.persistence.audit_repository import AuthAuditRepositoryAdapter
    from supabase import create_client

    provider_settings = settings.auth_provider
    if provider_settings is None:
        print("ERROR: Auth provider settings not configured.", file=sys.stderr)
        sys.exit(1)

    service_role_key = provider_settings.service_role_key.get_secret_value()
    provider_client = create_client(provider_settings.url, service_role_key)

    clock = SystemClock()
    identity_gen = SystemIdentity()

    session = session_factory()
    try:
        account_repo = AuthAccountRepositoryAdapter(session)
        audit_repo = AuthAuditRepositoryAdapter(session)
        identity_provider = IdentityProviderAdapter(provider_client, session)

        access_user_repo = AccessUserRepositoryAdapter(session)
        access_role_repo = RoleRepositoryAdapter(session)
        access_assignment_repo = AssignmentRepositoryAdapter(session)
        access_audit_repo = AccessAuditRepositoryAdapter(session)
        access_transaction = AccessTransactionAdapter(session)
        continuity = AdministratorContinuityAdapter(session)

        create_access_user = CreateAccessUser(
            user_repository=access_user_repo,
            role_repository=access_role_repo,
            assignment_repository=access_assignment_repo,
            audit_repository=access_audit_repo,
            transaction=access_transaction,
            clock=clock,
            identity=identity_gen,
        )
        activate_access_user = ActivateAccessUser(
            user_repository=access_user_repo,
            audit_repository=access_audit_repo,
            transaction=access_transaction,
            clock=clock,
        )
        deactivate_access_user = DeactivateAccessUser(
            user_repository=access_user_repo,
            audit_repository=access_audit_repo,
            transaction=access_transaction,
            clock=clock,
            continuity=continuity,
        )

        access_provisioning = AccessProvisioningAdapter(
            create_user=create_access_user,
            activate_user=activate_access_user,
            deactivate_user=deactivate_access_user,
            continuity=continuity,
        )

        bootstrap = BootstrapInitialAdministrator(
            account_repository=account_repo,
            audit_repository=audit_repo,
            identity_provider=identity_provider,
            access_provisioning=access_provisioning,
            clock=clock,
            identity=identity_gen,
        )

        account_id = bootstrap.execute(
            email=email,
            provisional_password=password,
            user_code=user_code,
            display_name=display_name,
        )
        session.commit()
        print(f"Bootstrap complete. Account ID: {account_id}")

    except (
        AccessError,
        AuthenticationError,
        OSError,
        SQLAlchemyError,
        ValueError,
    ) as exc:
        session.rollback()
        print(f"ERROR: Bootstrap failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
