from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from infra.configuration.cors_settings import CorsSettings
from infra.configuration.database_settings import DatabaseSettings
from infra.configuration.auth_provider_settings import AuthProviderSettings


class ApplicationSettings(BaseSettings):
    """Top-level application settings loaded from environment or .env file.

    Nested settings (e.g. database) are resolved from environment variables
    using the configured delimiter: ``DATABASE_URL`` maps to ``database.url``.

    ``cors`` is optional so that test environments (which inject a session
    factory directly) do not need CORS environment variables. Production
    startup validates its presence before wiring the CORS middleware.

    ``auth_provider`` is optional so that test environments without a running
    identity provider can still compose the app with injected doubles.
    Production startup validates its presence before wiring authentication.
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
    auth_provider: AuthProviderSettings | None = None

    def __init__(
        self,
        *,
        database: DatabaseSettings | None = None,
        cors: CorsSettings | None = None,
        auth_provider: AuthProviderSettings | None = None,
        _env_file: Path | None = None,
    ) -> None:
        """Load settings from explicit values, the environment, or a dotenv file."""
        if database is None and cors is None and auth_provider is None:
            # AuthProviderSettings uses its own env_prefix so it resolves independently.
            # pydantic-settings resolves fields from env vars at runtime.
            try:
                resolved_auth = AuthProviderSettings(
                    _env_file=_env_file,  # type: ignore[call-arg]
                )
            except Exception:
                resolved_auth = None
            super().__init__(
                _env_file=_env_file,  # type: ignore[call-arg]
                auth_provider=resolved_auth,
            )
            return
        kwargs: dict = {}
        if database is not None:
            kwargs["database"] = database
        if cors is not None:
            kwargs["cors"] = cors
        if auth_provider is not None:
            kwargs["auth_provider"] = auth_provider
        super().__init__(**kwargs, _env_file=_env_file)
