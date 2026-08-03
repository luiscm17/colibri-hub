from __future__ import annotations

import re
from dataclasses import dataclass


_EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$"
)


@dataclass(frozen=True, slots=True)
class NormalizedEmail:
    """Case-insensitive organizational email used as the unique login identifier.

    Validation ensures a structurally valid email. Actual mailbox ownership
    is confirmed outside Colibri Hub by the System Administrator.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or not _EMAIL_PATTERN.match(self.value):
            raise InvalidEmailError(self.value)
        normalized = self.value.strip().lower()
        if normalized != self.value:
            object.__setattr__(self, "value", normalized)

    @classmethod
    def from_raw(cls, raw: str) -> NormalizedEmail:
        """Create a NormalizedEmail from raw user input."""
        return cls(value=raw.strip().lower())


class InvalidEmailError(Exception):
    """The provided email is not structurally valid."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Invalid email format: '{email}'")
        self.email = email
