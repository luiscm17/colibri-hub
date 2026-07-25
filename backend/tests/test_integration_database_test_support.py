import os
import unittest
from unittest.mock import patch

from backend.integration_tests.database_test_support import create_test_engine


class TestDatabaseTestSupport(unittest.TestCase):
    def test_database_url_never_substitutes_for_missing_test_database_url(self) -> None:
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql+psycopg://user:secret@127.0.0.1:54322/postgres"},
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "TEST_DATABASE_URL"):
                create_test_engine()

    def test_rejects_non_local_postgresql_test_targets(self) -> None:
        invalid_urls = (
            "sqlite:///test.db",
            "postgresql+psycopg://user:secret@database.invalid:54322/postgres",
            "postgresql+psycopg://user:secret@127.0.0.1:54323/postgres",
            "postgresql+psycopg://user:secret@127.0.0.1:54322/not_postgres",
        )

        for url in invalid_urls:
            with self.subTest(url=url), patch.dict(
                os.environ, {"TEST_DATABASE_URL": url}, clear=True
            ):
                with self.assertRaisesRegex(RuntimeError, "TEST_DATABASE_URL"):
                    create_test_engine()


if __name__ == "__main__":
    unittest.main()
