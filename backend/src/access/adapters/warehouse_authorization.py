from access.application.services import AccessApplication, AccessDenied
from access.domain.models import Action, ScopeCode
from warehouse.bales.ports.authorization import (
    AuthenticatedIdentity,
    AuthorizationDenied,
)


class WarehouseAuthorizationAdapter:
    """Adapts Warehouse's consumer-owned port to Access policy decisions."""

    def __init__(self, access_application: AccessApplication) -> None:
        self._access_application = access_application

    def require(
        self, identity: AuthenticatedIdentity, *, action: str, scope: str
    ) -> None:
        try:
            self._access_application.authorize(
                identity.subject, Action(action), ScopeCode(scope)
            )
        except (AccessDenied, ValueError) as error:
            raise AuthorizationDenied("access_denied") from error
