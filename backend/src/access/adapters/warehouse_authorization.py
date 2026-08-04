"""Adapts Warehouse's consumer-owned authorization port to Access policy."""

from access.application.authorize_action import AuthorizeAction
from access.domain.errors import AccessDenied, AccessProfileNotFound, AccessUserInactive
from warehouse.bales.ports.authorization import (
    AuthenticatedIdentity,
    AuthorizationDenied,
)


class WarehouseAuthorizationAdapter:
    """Adapts Warehouse's consumer-owned port to Access authorization decisions."""

    def __init__(self, authorize_action: AuthorizeAction) -> None:
        self._authorize = authorize_action

    def require(
        self, identity: AuthenticatedIdentity, *, action: str, scope: str
    ) -> None:
        try:
            self._authorize.execute(
                subject=identity.subject, action=action, scope_code=scope
            )
        except (AccessDenied, AccessProfileNotFound, AccessUserInactive, ValueError) as error:
            raise AuthorizationDenied("access_denied") from error
