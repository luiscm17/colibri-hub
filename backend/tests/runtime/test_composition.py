import runpy
import os
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import cast
from unittest.mock import Mock, patch

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from bootstrap.http_application import create_app
from infra.configuration import ApplicationSettings, DatabaseSettings


def session_factory() -> Session:
    return cast(Session, Mock())


class ApplicationCompositionTests(unittest.TestCase):
    def test_default_settings_load_once_and_compose_router_and_handlers(self) -> None:
        database = DatabaseSettings(url="postgresql+psycopg://user:secret@host/database")
        default_settings = Mock(database=database)
        engine = cast(Engine, Mock())
        with patch("bootstrap.http_application.ApplicationSettings", return_value=default_settings) as load:
            app = create_app(
                settings_env_file=Path("configured.env"),
                engine_factory=Mock(return_value=engine),
                session_factory_builder=Mock(return_value=session_factory),
            )

        load.assert_called_once_with(_env_file=Path("configured.env"))
        self.assertIn("/api/v1/warehouse/bales", app.openapi()["paths"])
        self.assertIn(Exception, app.exception_handlers)

    def test_explicit_settings_and_engine_bypass_the_lower_unneeded_layer(self) -> None:
        settings = ApplicationSettings(
            database=DatabaseSettings(url="postgresql+psycopg://user:secret@host/database")
        )
        engine = cast(Engine, Mock())
        factory_builder: Callable[[Engine], Callable[[], Session]] = Mock(
            return_value=session_factory
        )
        engine_factory: Callable[[DatabaseSettings], Engine] = Mock(return_value=engine)
        with patch("bootstrap.http_application.ApplicationSettings", side_effect=AssertionError):
            create_app(settings=settings, engine_factory=engine_factory, session_factory_builder=factory_builder)
            create_app(engine=engine, session_factory_builder=factory_builder)
        engine_factory.assert_called_once_with(settings.database)

    def test_injected_session_factory_bypasses_all_settings_and_database_construction(self) -> None:
        with patch("bootstrap.http_application.ApplicationSettings", side_effect=AssertionError):
            app = create_app(
                session_factory=session_factory,
                engine_factory=Mock(side_effect=AssertionError),
                session_factory_builder=Mock(side_effect=AssertionError),
            )
        self.assertIn("/api/v1/warehouse/bales", app.openapi()["paths"])

    def test_entrypoint_passes_its_adjacent_env_path_without_reading_dotenv(self) -> None:
        main_path = Path(__file__).parents[2] / "main.py"
        with tempfile.TemporaryDirectory() as directory:
            original_directory = Path.cwd()
            os.chdir(directory)
            try:
                with patch("bootstrap.http_application.create_app") as create_app_spy:
                    runpy.run_path(main_path)
            finally:
                os.chdir(original_directory)
        create_app_spy.assert_called_once_with(settings_env_file=main_path.with_name(".env"))
