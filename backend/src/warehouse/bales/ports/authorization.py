from typing import Protocol

from shared.identity import AuthenticatedIdentity as AuthenticatedIdentity
from shared.identity import IdentityResolver as IdentityResolver


class AuthorizationDenied(Exception):
    """A business denial which intentionally exposes no policy details."""


class AuthorizationPort(Protocol):
    """Warehouse's narrow authorization dependency."""

    def require(
        self, identity: AuthenticatedIdentity, *, action: str, scope: str
    ) -> None: ...
