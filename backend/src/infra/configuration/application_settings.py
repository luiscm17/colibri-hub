from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from infra.configuration.database_settings import DatabaseSettings


class ApplicationSettings(BaseSettings):
    """Top-level application settings loaded from environment or .env file.

    Nested settings (e.g. database) are resolved from environment variables
    using the configured delimiter: ``DATABASE_URL`` maps to ``database.url``.
    """

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,
    )

    database: DatabaseSettings

    def __init__(
        self,
        *,
        database: DatabaseSettings | None = None,
        _env_file: Path | None = None,
    ) -> None:
        """Load settings from explicit values, the environment, or a dotenv file."""
        if database is None:
            super().__init__(_env_file=_env_file)
            return
        super().__init__(database=database, _env_file=_env_file)
