from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    """Trusted, provider-neutral identity supplied by Authentication."""

    subject: str
    session_id: str | None = None


IdentityResolver = Callable[..., AuthenticatedIdentity]


class AuthorizationDenied(Exception):
    """A business denial which intentionally exposes no policy details."""


class AuthorizationPort(Protocol):
    """Warehouse's narrow authorization dependency."""

    def require(
        self, identity: AuthenticatedIdentity, *, action: str, scope: str
    ) -> None: ...
