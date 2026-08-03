from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from bootstrap.database_session_dependency import (
    SessionFactory,
    session_dependency,
)
from bootstrap.api_router import create_api_router
from bootstrap.http_error_handlers import register_exception_handlers
from bootstrap.warehouse_bale_dependency import (
    access_application_dependency,
    use_case_dependency,
)
from access.adapters.http_router import AccessApplicationProvider
from access.adapters.warehouse_authorization import WarehouseAuthorizationAdapter
from access.application.services import AccessApplication
from infra.configuration import ApplicationSettings, DatabaseSettings
from infra.persistence.database_engine import create_db_engine
from infra.persistence.database_session_factory import create_session_factory
from warehouse.bales.ports.authorization import (
    AuthenticatedIdentity,
    AuthorizationPort,
    IdentityResolver,
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
    identity_resolver: IdentityResolver = unauthenticated_identity,
) -> FastAPI:
    """Create and configure the FastAPI application.
    
    Composes settings, database engine, session factory, exception handlers,
    and all API routes. Accepts optional overrides for testability.
    
    Args:
        settings: Pre-resolved application settings. Resolved from env if omitted.
        settings_env_file: Optional .env file path for settings resolution.
        engine: Pre-built database engine. Created from settings if omitted.
        session_factory: Pre-built session factory. Created from engine if omitted.
        engine_factory: Factory to create an engine (injectable for testing).
        session_factory_builder: Factory to create a session factory (injectable).
    
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
    access_application_provider = access_application_dependency(session_provider)

    def authorization_provider(
        access_application: Annotated[
            AccessApplication, Depends(access_application_provider)
        ],
    ) -> AuthorizationPort:
        return WarehouseAuthorizationAdapter(access_application)

    app = FastAPI()

    if resolved_settings is not None and resolved_settings.cors is not None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=resolved_settings.cors.allowed_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "Authorization"],
        )

    register_exception_handlers(app)

    app.include_router(
        create_api_router(
            use_case_provider,
            identity_resolver,
            authorization_provider,
            access_application_provider,
        )
    )
    return app
