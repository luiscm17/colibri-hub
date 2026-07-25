import re

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator


class DatabaseSettings(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    url: SecretStr

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, value: object) -> str:
        if isinstance(value, SecretStr):
            value = value.get_secret_value()
        if not isinstance(value, str):
            raise ValueError("Database URL must be a non-empty URL")
        url = value.strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*://\S+", url):
            raise ValueError("Database URL must be a non-empty URL")
        return url
