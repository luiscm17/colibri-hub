"""Provider-neutral identity types shared across bounded contexts."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    """Trusted, provider-neutral identity supplied by Authentication."""

    subject: str
    session_id: str | None = None


IdentityResolver = Callable[..., AuthenticatedIdentity]
