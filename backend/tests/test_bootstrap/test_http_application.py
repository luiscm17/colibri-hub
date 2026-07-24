import importlib
import os
import sys
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from bootstrap.database_session_dependency import (
    session_dependency,
)
from bootstrap.api_router import create_api_router
from bootstrap.http_application import create_app
from bootstrap.warehouse_bale_dependency import build_use_case
from infra.persistence.database_settings import DatabaseSettings
from warehouse.application.raw_material.bale_reception_errors import (
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
)
from warehouse.adapters.http.raw_material.bale_router import (
    create_router as create_bale_router,
)
from warehouse.adapters.http.router import create_router as create_warehouse_router


class FakeSession(Session):
    def __init__(self) -> None:
        self.closed = False

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *args: object) -> None:
        self.closed = True


class TestBootstrapDependencies(unittest.TestCase):
    def test_assembled_use_case_shares_one_session(self) -> None:
        session = FakeSession()

        use_case = build_use_case(session)

        self.assertIs(getattr(use_case._reception_repository, "_session"), session)
        self.assertIs(getattr(use_case._bale_repository, "_session"), session)
        self.assertIs(getattr(use_case._warehouse_transaction, "_session"), session)

    def test_session_dependency_yields_and_closes_independent_sessions(self) -> None:
        sessions: list[FakeSession] = []

        def session_factory() -> FakeSession:
            session = FakeSession()
            sessions.append(session)
            return session

        dependency = session_dependency(session_factory)

        for expected_index in range(2):
            generator = dependency()
            yielded = next(generator)
            self.assertIs(yielded, sessions[expected_index])
            self.assertFalse(sessions[expected_index].closed)
            generator.close()
            self.assertTrue(sessions[expected_index].closed)

        self.assertIsNot(sessions[0], sessions[1])


class TestHttpApplication(unittest.TestCase):
    def test_router_hierarchy_assigns_each_prefix_to_one_owner(self) -> None:
        from typing import Any, Callable

        use_case_provider: Callable[[], Any] = lambda: object()

        api_router = create_api_router(use_case_provider)
        warehouse_router = create_warehouse_router(use_case_provider)
        bale_router = create_bale_router(use_case_provider)

        self.assertEqual(api_router.prefix, "/api/v1")
        self.assertEqual(warehouse_router.prefix, "/warehouse")
        self.assertEqual(bale_router.prefix, "/bales")

    def test_factory_exposes_exact_route_without_database_access(self) -> None:
        session_factory_calls = 0

        def session_factory() -> FakeSession:
            nonlocal session_factory_calls
            session_factory_calls += 1
            return FakeSession()

        with patch.dict(os.environ, {}, clear=True):
            app = create_app(session_factory=session_factory)

        post_paths = [
            path
            for path, operations in app.openapi()["paths"].items()
            if "post" in operations
        ]
        self.assertEqual(post_paths, ["/api/v1/warehouse/bales"])
        self.assertEqual(session_factory_calls, 0)

        client = TestClient(app)
        response = client.post("/api/v1/warehouse/bales", json={})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.history, [])
        self.assertEqual(session_factory_calls, 1)

        slash_response = client.post(
            "/api/v1/warehouse/bales/",
            json={},
            follow_redirects=False,
        )
        self.assertEqual(slash_response.status_code, 307)
        self.assertEqual(
            slash_response.headers["location"],
            "http://testserver/api/v1/warehouse/bales",
        )

    def test_create_app_with_explicit_engine(self) -> None:
        engine = create_engine("sqlite:///:memory:", echo=True)

        app = create_app(engine=engine)

        self.assertIsInstance(app, FastAPI)
        post_paths = {
            path
            for path, operations in app.openapi()["paths"].items()
            if "post" in operations
        }
        self.assertEqual(post_paths, {"/api/v1/warehouse/bales"})

    def test_create_app_with_explicit_settings(self) -> None:
        settings = DatabaseSettings(
            database_url="sqlite:///:memory:",
        )

        app = create_app(settings=settings)

        self.assertIsInstance(app, FastAPI)
        post_paths = {
            path
            for path, operations in app.openapi()["paths"].items()
            if "post" in operations
        }
        self.assertEqual(post_paths, {"/api/v1/warehouse/bales"})

    def test_registers_exception_handlers(self) -> None:
        def session_factory() -> Session:
            return Session()

        app = create_app(session_factory=session_factory)

        handler_types = {exc for exc in app.exception_handlers if isinstance(exc, type)}

        self.assertIn(DuplicateShipmentNumberError, handler_types)
        self.assertIn(DuplicateBaleNumberError, handler_types)

    def test_backend_main_exposes_app_without_opening_connection(self) -> None:
        database_url = (
            "postgresql+psycopg://fixture_user:fixture_password@"
            "database.invalid/fixture_database"
        )
        sys.modules.pop("backend.main", None)

        with patch.dict(os.environ, {"DATABASE_URL": database_url}, clear=True):
            module = importlib.import_module("backend.main")

        self.assertIsInstance(module.app, FastAPI)


if __name__ == "__main__":
    unittest.main()
