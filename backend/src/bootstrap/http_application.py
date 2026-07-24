from collections.abc import Callable

from fastapi import FastAPI
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from bootstrap.database_session_dependency import (
    SessionFactory,
    session_dependency,
)
from bootstrap.http_error_handlers import register_exception_handlers
from bootstrap.warehouse_bale_dependency import (
    use_case_dependency,
)
from infra.persistence.database_engine import create_db_engine
from infra.persistence.database_session_factory import create_session_factory
from infra.persistence.database_settings import DatabaseSettings
from warehouse.adapters.http.raw_material.bale_router import create_router

EngineFactory = Callable[[DatabaseSettings], Engine]
SessionFactoryBuilder = Callable[[Engine], Callable[[], Session]]


def create_app(
    *,
    settings: DatabaseSettings | None = None,
    engine: Engine | None = None,
    session_factory: SessionFactory | None = None,
    engine_factory: EngineFactory = create_db_engine,
    session_factory_builder: SessionFactoryBuilder = create_session_factory,
) -> FastAPI:
    if session_factory is None:
        if engine is None:
            resolved_settings = settings or DatabaseSettings.from_env()
            engine = engine_factory(resolved_settings)
        session_factory = session_factory_builder(engine)

    session_provider = session_dependency(session_factory)
    use_case_provider = use_case_dependency(session_provider)

    app = FastAPI()

    register_exception_handlers(app)

    app.include_router(
        create_router(use_case_provider),
        prefix="/api/v1/warehouse/bales",
    )
    return app
