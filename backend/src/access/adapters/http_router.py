"""Access Control HTTP router: self-access endpoint.

Administrative endpoints are added in PR 4.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from access.application.get_current_access import GetCurrentAccess
from access.domain.actions import Action
from access.domain.errors import AccessProfileNotFound, AccessUserInactive
from warehouse.bales.ports.authorization import (
    AuthenticatedIdentity,
    IdentityResolver,
)


GetCurrentAccessProvider = Callable[..., GetCurrentAccess]


def create_access_router(
    identity_resolver: IdentityResolver,
    get_current_access_provider: GetCurrentAccessProvider,
) -> APIRouter:
    """Create the self-access HTTP adapter."""
    router = APIRouter(prefix="/access")

    @router.get("/me")
    def current_access(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_case: Annotated[GetCurrentAccess, Depends(get_current_access_provider)],
    ) -> dict[str, object]:
        try:
            result = use_case.execute(subject=identity.subject)
        except AccessProfileNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="profile_not_found",
            )
        except AccessUserInactive:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="profile_inactive",
            )

        if result.is_global:
            return {
                "user_id": result.user_id,
                "user_code": result.user_code,
                "display_name": result.display_name,
                "is_active": result.is_active,
                "authorization": {
                    "global": True,
                    "actions": sorted(a.value for a in Action),
                    "permissions": [],
                    "version": result.authorization_version,
                },
            }

        return {
            "user_id": result.user_id,
            "user_code": result.user_code,
            "display_name": result.display_name,
            "is_active": result.is_active,
            "authorization": {
                "global": False,
                "permissions": [
                    {"action": p.action, "scope": p.scope_code}
                    for p in result.permissions
                ],
                "version": result.authorization_version,
            },
        }

    return router
