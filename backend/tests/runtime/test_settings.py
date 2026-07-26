import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from infra.configuration import ApplicationSettings, DatabaseSettings


FILE_URL = "postgresql+psycopg://file-user:file-secret@file-host/test"
OS_URL = "postgresql+psycopg://os-user:os-secret@os-host/test"


class ApplicationSettingsTests(unittest.TestCase):
    def test_explicit_env_file_is_used_and_os_environment_overrides_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / "settings.env"
            env_file.write_text(f"DATABASE_URL={FILE_URL}\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(
                    ApplicationSettings(_env_file=env_file).database.url.get_secret_value(),
                    FILE_URL,
                )
            with patch.dict(os.environ, {"DATABASE_URL": OS_URL}, clear=True):
                self.assertEqual(
                    ApplicationSettings(_env_file=env_file).database.url.get_secret_value(),
                    OS_URL,
                )

    def test_absent_or_implicit_dotenv_never_overrides_isolated_os_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            dotenv = Path(directory) / ".env"
            dotenv.write_text(f"DATABASE_URL={FILE_URL}\n", encoding="utf-8")
            with patch.dict(os.environ, {"DATABASE_URL": OS_URL}, clear=True):
                original_directory = Path.cwd()
                os.chdir(directory)
                try:
                    settings = ApplicationSettings(
                        _env_file=Path(directory) / "missing.env"
                    )
                finally:
                    os.chdir(original_directory)
        self.assertEqual(settings.database.url.get_secret_value(), OS_URL)

    def test_database_url_validation_and_secret_redaction_are_observable(self) -> None:
        secret_url = "postgresql+psycopg://user:private-password@host/database"
        settings = DatabaseSettings(url=secret_url)

        self.assertIn("**********", repr(settings))
        self.assertNotIn("private-password", repr(settings))
        for invalid_url in ("", "   ", "not a url"):
            with self.subTest(invalid_url=invalid_url):
                with self.assertRaises(ValidationError) as raised:
                    DatabaseSettings(url=invalid_url)
                self.assertIn("Database URL must be a non-empty URL", str(raised.exception))
        with self.assertRaises(ValidationError) as raised:
            DatabaseSettings(url="private-password is not a URL")
        self.assertNotIn("private-password", str(raised.exception))
