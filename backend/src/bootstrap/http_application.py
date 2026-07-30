from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI
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
    use_case_dependency,
)
from infra.configuration import ApplicationSettings, DatabaseSettings
from infra.persistence.database_engine import create_db_engine
from infra.persistence.database_session_factory import create_session_factory

EngineFactory = Callable[[DatabaseSettings], Engine]
"""Type alias for a factory that creates a database Engine from settings."""

SessionFactoryBuilder = Callable[[Engine], Callable[[], Session]]
"""Type alias for a factory that builds a session factory from an Engine."""


def create_app(
    *,
    settings: ApplicationSettings | None = None,
    settings_env_file: Path | None = None,
    engine: Engine | None = None,
    session_factory: SessionFactory | None = None,
    engine_factory: EngineFactory = create_db_engine,
    session_factory_builder: SessionFactoryBuilder = create_session_factory,
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

    app = FastAPI()

    if resolved_settings is not None and resolved_settings.cors is not None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=resolved_settings.cors.allowed_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )

    register_exception_handlers(app)

    app.include_router(create_api_router(use_case_provider))
    return app
