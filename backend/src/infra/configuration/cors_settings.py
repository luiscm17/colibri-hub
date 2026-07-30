from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CorsSettings(BaseSettings):
    """CORS configuration loaded from environment variables.

    Validates that each origin is a proper scheme+host(+port) URL,
    that at least one origin is provided, and that wildcard is not used.
    """

    model_config = SettingsConfigDict(
        env_prefix="CORS_",
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    allowed_origins: list[str]

    @field_validator("allowed_origins")
    @classmethod
    def validate_origins(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one CORS origin is required.")
        for origin in v:
            if origin == "*":
                raise ValueError("Wildcard origin is not allowed.")
            parsed = urlparse(origin)
            if not parsed.scheme or not parsed.netloc or parsed.path not in ("", "/"):
                raise ValueError(f"Invalid origin: {origin}")
        return v
