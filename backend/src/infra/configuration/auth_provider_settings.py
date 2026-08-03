"""Authentication provider configuration for backend identity services."""

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator


class AuthProviderSettings(BaseModel):
    """Authentication provider connection settings.

    Required for the Authentication capability. Startup fails clearly
    when these values are absent.

    Attributes:
        url: Provider project URL (e.g. http://127.0.0.1:54321).
        service_role_key: Server-only admin key. Never exposed to frontend.
        jwt_secret: Shared HMAC secret for local JWT validation.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    url: str
    service_role_key: SecretStr
    jwt_secret: SecretStr

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, value: object) -> str:
        if isinstance(value, str) and value.strip().startswith("http"):
            return value.strip().rstrip("/")
        raise ValueError("Provider URL must be a valid HTTP(S) URL")
