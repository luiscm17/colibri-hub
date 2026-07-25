from pydantic_settings import BaseSettings, SettingsConfigDict

from infra.configuration.database_settings import DatabaseSettings


class ApplicationSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,
    )

    database: DatabaseSettings
