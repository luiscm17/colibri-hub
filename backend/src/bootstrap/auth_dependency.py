"""FastAPI dependency factory for Authentication use cases.

Composes the real authentication stack: JWT token validation as the identity
resolver and a typed AuthUseCases container built per-request with shared
SQLAlchemy session scope (preserving access-provisioning session sharing).
"""

from collections.abc import Callable
from typing import Annotated

from auth.adapters.identity_provider.admin_client import IdentityProviderAdapter
from auth.adapters.identity_provider.jwt_validator import TokenValidatorAdapter
from auth.adapters.persistence.account_repository import AuthAccountRepositoryAdapter
from auth.adapters.persistence.audit_repository import AuthAuditRepositoryAdapter
from auth.application.change_required_password import ChangeRequiredPassword
from auth.application.auth_use_cases import AuthUseCases, AuthUseCaseProvider
from auth.application.disable_account import DisableAccount
from auth.application.enable_account import EnableAccount
from auth.application.get_account import GetAccount
from auth.application.get_current_authentication import GetCurrentAuthentication
from auth.application.list_accounts import ListAccounts
from auth.application.list_audits import ListAudits
from auth.application.provision_account import ProvisionAccount
from auth.application.record_logout import RecordLogout
from auth.application.reset_password import ResetPassword
from fastapi import Depends, Request
from infra.clock import SystemClock
from infra.configuration import ApplicationSettings
from infra.identity import SystemIdentity
from infra.persistence.record_registry import register_auth_records
from shared.identity import AuthenticatedIdentity, IdentityResolver
from sqlalchemy.orm import Session
from supabase import create_client

from bootstrap.database_session_dependency import SessionProvider


def compose_auth(
    settings: ApplicationSettings,
    session_provider: SessionProvider,
) -> tuple[IdentityResolver, AuthUseCaseProvider]:
    """Compose the real authentication stack from provider settings.

    Returns the identity resolver (JWT validator) and the auth use case
    factory that builds a typed AuthUseCases container per request.

    Session-sharing with access provisioning is preserved: the same
    SQLAlchemy session feeds both auth and access repositories within
    a single request scope.
    """
    register_auth_records()

    provider_settings = settings.auth_provider
    assert provider_settings is not None

    jwt_secret = provider_settings.jwt_secret.get_secret_value()
    service_role_key = provider_settings.service_role_key.get_secret_value()

    # Create admin client for server-side identity operations
    provider_client = create_client(provider_settings.url, service_role_key)
    identity_provider = IdentityProviderAdapter(provider_client)

    # Token validator as the identity resolver (JWKS preferred, HMAC fallback)
    jwks_url = f"{provider_settings.url}/auth/v1/.well-known/jwks.json"
    token_validator = TokenValidatorAdapter(
        jwks_url=jwks_url,
        jwt_secret=jwt_secret,
    )

    def identity_resolver(request: Request) -> AuthenticatedIdentity:
        return token_validator.resolve_identity(request)

    # Shared infra adapters
    clock = SystemClock()
    identity_gen = SystemIdentity()

    def auth_use_case_factory(
        session: Annotated[Session, Depends(session_provider)],
    ) -> AuthUseCases:
        account_repo = AuthAccountRepositoryAdapter(session)
        audit_repo = AuthAuditRepositoryAdapter(session)

        # Build the real Access provisioning adapter sharing this session
        from access.adapters.access_provisioning import AccessProvisioningAdapter
        from access.adapters.persistence.audit_repository import (
            AccessAuditRepositoryAdapter,
        )
        from access.adapters.persistence.user_repository import (
            AccessUserRepositoryAdapter,
        )
        from access.adapters.persistence.assignment_repository import (
            AssignmentRepositoryAdapter,
        )
        from access.adapters.persistence.role_repository import (
            RoleRepositoryAdapter,
        )
        from access.adapters.persistence.transaction import (
            TransactionAdapter as AccessTransactionAdapter,
        )
        from access.application.activate_access_user import ActivateAccessUser
        from access.application.create_access_user import CreateAccessUser
        from access.application.deactivate_access_user import DeactivateAccessUser

        access_user_repo = AccessUserRepositoryAdapter(session)
        access_role_repo = RoleRepositoryAdapter(session)
        access_assignment_repo = AssignmentRepositoryAdapter(session)
        access_audit_repo = AccessAuditRepositoryAdapter(session)
        access_transaction = AccessTransactionAdapter(session)

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
        )

        access_provisioning = AccessProvisioningAdapter(
            create_user=create_access_user,
            activate_user=activate_access_user,
            deactivate_user=deactivate_access_user,
            user_repository=access_user_repo,
        )

        return AuthUseCases(
            get_current_authentication=GetCurrentAuthentication(account_repo),
            change_required_password=ChangeRequiredPassword(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                clock=clock,
                identity=identity_gen,
            ),
            record_logout=RecordLogout(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                clock=clock,
                identity=identity_gen,
            ),
            provision_account=ProvisionAccount(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                access_provisioning=access_provisioning,
                clock=clock,
                identity=identity_gen,
            ),
            reset_password=ResetPassword(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                access_provisioning=access_provisioning,
                clock=clock,
                identity=identity_gen,
            ),
            disable_account=DisableAccount(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                access_provisioning=access_provisioning,
                clock=clock,
                identity=identity_gen,
            ),
            enable_account=EnableAccount(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                access_provisioning=access_provisioning,
                clock=clock,
                identity=identity_gen,
            ),
            get_account=GetAccount(account_repo),
            list_accounts=ListAccounts(account_repo),
            list_audits=ListAudits(audit_repo, account_repo, identity_provider, clock),
        )

    return identity_resolver, auth_use_case_factory
