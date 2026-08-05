from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI, HTTPException
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
        from bootstrap.auth_dependency import compose_auth

        resolved_identity_resolver, auth_use_case_provider = (
            compose_auth(resolved_settings, session_provider)
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


