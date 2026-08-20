"""Deterministic checks for local Supabase authentication configuration."""

import tomllib
import unittest
from pathlib import Path


class LocalSupabaseAuthConfigurationTests(unittest.TestCase):
    def test_session_timebox_is_eight_hours(self) -> None:
        config = tomllib.loads(Path("supabase/config.toml").read_text())
        self.assertEqual(config["auth"]["sessions"]["timebox"], "8h")


if __name__ == "__main__":
    unittest.main()
