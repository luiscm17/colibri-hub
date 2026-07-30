from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from infra.configuration.cors_settings import CorsSettings
from infra.configuration.database_settings import DatabaseSettings


class ApplicationSettings(BaseSettings):
    """Top-level application settings loaded from environment or .env file.

    Nested settings (e.g. database) are resolved from environment variables
    using the configured delimiter: ``DATABASE_URL`` maps to ``database.url``.

    ``cors`` is optional so that test environments (which inject a session
    factory directly) do not need CORS environment variables. Production
    startup validates its presence before wiring the CORS middleware.
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
    cors: CorsSettings | None = None

    def __init__(
        self,
        *,
        database: DatabaseSettings | None = None,
        cors: CorsSettings | None = None,
        _env_file: Path | None = None,
    ) -> None:
        """Load settings from explicit values, the environment, or a dotenv file."""
        if database is None and cors is None:
            super().__init__(_env_file=_env_file)
            return
        kwargs: dict = {}
        if database is not None:
            kwargs["database"] = database
        if cors is not None:
            kwargs["cors"] = cors
        super().__init__(**kwargs, _env_file=_env_file)
