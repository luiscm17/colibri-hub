import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from infra.configuration import ApplicationSettings, DatabaseSettings


URL = "postgresql+psycopg://user:secret@database.invalid/app"


class TestApplicationSettings(unittest.TestCase):
    def test_maps_database_url_to_nested_secret_settings(self) -> None:
        settings = ApplicationSettings(database={"url": URL})

        self.assertEqual(settings.database.url.get_secret_value(), URL)
        self.assertIn("**********", repr(settings))
        self.assertNotIn("secret", repr(settings))
        with self.assertRaises(ValidationError):
            DatabaseSettings(url=URL, unexpected="value")
        with self.assertRaises(ValidationError):
            settings.database.url = URL  # type: ignore[misc]

    def test_rejects_missing_blank_and_malformed_urls_without_leaking_input(self) -> None:
        for value in (None, "", "   ", "postgresql missing secret"):
            with self.subTest(value=value), self.assertRaises(ValidationError) as error:
                ApplicationSettings(_env_file=None, database={"url": value})
            self.assertNotIn("secret", str(error.exception))

    def test_os_environment_overrides_an_explicit_dotenv_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            dotenv = Path(directory, ".env")
            dotenv.write_text("DATABASE_URL=sqlite:///dotenv.db\n")
            with patch.dict(os.environ, {"DATABASE_URL": URL}, clear=True):
                settings = ApplicationSettings(_env_file=dotenv)

        self.assertEqual(settings.database.url.get_secret_value(), URL)

    def test_explicit_file_is_cwd_independent_and_missing_file_is_os_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dotenv = root / "backend.env"
            dotenv.write_text("DATABASE_URL=sqlite:///explicit.db\n")
            unrelated = root / "nested"
            unrelated.mkdir()
            (root / ".env").write_text(f"DATABASE_URL={URL}\n")
            with patch.dict(os.environ, {}, clear=True), patch("os.getcwd", return_value=str(unrelated)):
                settings = ApplicationSettings(_env_file=dotenv)
            with patch.dict(os.environ, {"DATABASE_URL": URL}, clear=True):
                absent = ApplicationSettings(_env_file=root / "absent.env")

        self.assertEqual(settings.database.url.get_secret_value(), "sqlite:///explicit.db")
        self.assertEqual(absent.database.url.get_secret_value(), URL)

    def test_no_env_file_uses_only_os_environment(self) -> None:
        with patch.dict(os.environ, {"DATABASE_URL": URL}, clear=True):
            settings = ApplicationSettings(_env_file=None)

        self.assertEqual(settings.database.url.get_secret_value(), URL)


if __name__ == "__main__":
    unittest.main()
