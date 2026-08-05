from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from infra.configuration import ApplicationSettings, DatabaseSettings
from infra.persistence.database_engine import create_db_engine
from infra.persistence.database_session_factory import create_session_factory
from shared.identity import AuthenticatedIdentity, IdentityResolver
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from bootstrap.api_router import create_api_router
from bootstrap.database_session_dependency import (
    SessionFactory,
    session_dependency,
)
from bootstrap.http_error_handlers import register_exception_handlers
from bootstrap.warehouse_bale_dependency import (
    authorization_provider_dependency,
    authorize_action_dependency,
    get_current_access_dependency,
    use_case_dependency,
)

EngineFactory = Callable[[DatabaseSettings], Engine]
"""Type alias for a factory that creates a database Engine from settings."""

SessionFactoryBuilder = Callable[[Engine], Callable[[], Session]]
"""Type alias for a factory that builds a session factory from an Engine."""


def unauthenticated_identity() -> AuthenticatedIdentity:
    """Fail closed until Authentication provides a validated identity."""
    raise HTTPException(status_code=401, detail="authentication_required")


def create_app(
    *,
    settings: ApplicationSettings | None = None,
    settings_env_file: Path | None = None,
    engine: Engine | None = None,
    session_factory: SessionFactory | None = None,
    engine_factory: EngineFactory = create_db_engine,
    session_factory_builder: SessionFactoryBuilder = create_session_factory,
    identity_resolver: IdentityResolver | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    When auth provider settings are present and no explicit identity_resolver is
    provided, composes the real TokenValidatorAdapter as the identity resolver
    and mounts the auth HTTP router with real use cases.

    Args:
        settings: Pre-resolved application settings. Resolved from env if omitted.
        settings_env_file: Optional .env file path for settings resolution.
        engine: Pre-built database engine. Created from settings if omitted.
        session_factory: Pre-built session factory. Created from engine if omitted.
        engine_factory: Factory to create an engine (injectable for testing).
        session_factory_builder: Factory to create a session factory (injectable).
        identity_resolver: Override identity resolution (for testing). When None,
            uses TokenValidatorAdapter if auth provider config is present, otherwise
            fails closed with 401.

    Returns:
        Configured FastAPI application ready to serve requests.
    """
    resolved_settings: ApplicationSettings | None = settings

    if session_factory is None:
        if engine is None:
            resolved_settings = settings or ApplicationSettings(
                _env_file=settings_env_file
            )
            engine = engine_factory(resolved_settings.database)
        session_factory = session_factory_builder(engine)

    session_provider = session_dependency(session_factory)
    use_case_provider = use_case_dependency(session_provider)
    get_current_access_provider = get_current_access_dependency(session_provider)
    authorize_action_provider = authorize_action_dependency(session_provider)
    authorization_provider = authorization_provider_dependency(session_provider)

    # Resolve identity resolver and auth use case provider
    auth_use_case_provider = None

    if identity_resolver is not None:
        resolved_identity_resolver = identity_resolver
    elif resolved_settings is not None and resolved_settings.auth_provider is not None:
        resolved_identity_resolver, auth_use_case_provider = (
            _compose_auth(resolved_settings, session_provider)
        )
    else:
        resolved_identity_resolver = unauthenticated_identity

    app = FastAPI()

    if resolved_settings is not None and resolved_settings.cors is not None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=resolved_settings.cors.allowed_origins,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Content-Type", "Authorization"],
        )

    register_exception_handlers(app)

    # Build admin use case provider if auth is configured
    admin_use_case_provider = None
    if auth_use_case_provider is not None:
        from bootstrap.access_admin_dependency import admin_use_case_dependency
        admin_use_case_provider = admin_use_case_dependency(session_provider)

    app.include_router(
        create_api_router(
            use_case_provider,
            resolved_identity_resolver,
            authorization_provider,
            get_current_access_provider,
            authorize_action_provider,
            admin_use_case_provider,
            auth_use_case_provider,
        )
    )
    return app


def _compose_auth(
    settings: ApplicationSettings,
    session_provider: Callable,
) -> tuple[IdentityResolver, Callable]:
    """Compose the real authentication stack from provider settings.

    Returns the identity resolver (JWT validator) and the auth use case factory.
    """
    from auth.adapters.identity_provider.admin_client import IdentityProviderAdapter
    from auth.adapters.identity_provider.jwt_validator import TokenValidatorAdapter
    from auth.adapters.persistence.repositories import (
        AccountRepositoryAdapter,
        AuditRepositoryAdapter,
    )
    from auth.application.change_required_password import ChangeRequiredPassword
    from auth.application.disable_account import DisableAccount
    from auth.application.enable_account import EnableAccount
    from auth.application.get_account import GetAccount
    from auth.application.get_current_authentication import GetCurrentAuthentication
    from auth.application.list_accounts import ListAccounts
    from auth.application.list_audits import ListAudits
    from auth.application.provision_account import ProvisionAccount
    from auth.application.record_logout import RecordLogout
    from auth.application.reset_password import ResetPassword
    from infra.persistence.record_registry import register_auth_records

    from supabase import create_client

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

    # Auth use case factory (builds fresh use cases per request with DB session)
    class _FakeClock:
        def now(self):
            from datetime import datetime, timezone
            return datetime.now(timezone.utc)

    class _FakeIdentity:
        def generate_id(self):
            from uuid import uuid4
            return str(uuid4())

        def generate_operation_id(self):
            from uuid import uuid4
            return str(uuid4())

    clock = _FakeClock()
    identity_gen = _FakeIdentity()

    def auth_use_case_factory(
        session: Annotated[Session, Depends(session_provider)],
    ) -> dict:
        account_repo = AccountRepositoryAdapter(session)
        audit_repo = AuditRepositoryAdapter(session)

        # Build the real Access provisioning adapter sharing this session
        from access.adapters.access_provisioning import AccessProvisioningAdapter
        from access.adapters.persistence.repositories import (
            AccessAuditRepositoryAdapter,
            AccessUserRepositoryAdapter,
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
        access_audit_repo = AccessAuditRepositoryAdapter(session)
        access_transaction = AccessTransactionAdapter(session)

        create_access_user = CreateAccessUser(
            user_repository=access_user_repo,
            role_repository=access_role_repo,
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

        return {
            "get_current_authentication": GetCurrentAuthentication(account_repo),
            "change_required_password": ChangeRequiredPassword(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                clock=clock,
                identity=identity_gen,
            ),
            "record_logout": RecordLogout(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                clock=clock,
                identity=identity_gen,
            ),
            "provision_account": ProvisionAccount(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                access_provisioning=access_provisioning,
                clock=clock,
                identity=identity_gen,
            ),
            "reset_password": ResetPassword(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                access_provisioning=access_provisioning,
                clock=clock,
                identity=identity_gen,
            ),
            "disable_account": DisableAccount(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                access_provisioning=access_provisioning,
                clock=clock,
                identity=identity_gen,
            ),
            "enable_account": EnableAccount(
                account_repository=account_repo,
                audit_repository=audit_repo,
                identity_provider=identity_provider,
                access_provisioning=access_provisioning,
                clock=clock,
                identity=identity_gen,
            ),
            "get_account": GetAccount(account_repo),
            "list_accounts": ListAccounts(account_repo),
            "list_audits": ListAudits(audit_repo),
        }

    return identity_resolver, auth_use_case_factory
