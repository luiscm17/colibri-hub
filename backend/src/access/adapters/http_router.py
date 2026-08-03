from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from access.application.services import AccessApplication
from warehouse.bales.ports.authorization import (
    AuthenticatedIdentity,
    IdentityResolver,
)


AccessApplicationProvider = Callable[..., AccessApplication]


def create_access_router(
    identity_resolver: IdentityResolver,
    access_application_provider: AccessApplicationProvider,
) -> APIRouter:
    """Create the minimal self-access HTTP adapter."""
    router = APIRouter(prefix="/access")

    @router.get("/me")
    def current_access(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        access_application: Annotated[
            AccessApplication, Depends(access_application_provider)
        ],
    ) -> dict[str, object]:
        state = access_application._store.load()
        profile = next(
            (item for item in state.profiles if item.subject == identity.subject),
            None,
        )
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile_not_found")
        if not profile.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="profile_inactive")

        snapshot = access_application.current_access(identity.subject, state)
        assert snapshot is not None
        return {
            "subject": snapshot.subject,
            "profile_code": snapshot.profile_code,
            "global": snapshot.global_access,
            "permissions": [
                {"action": permission.action.value, "scope": permission.scope.value}
                for permission in sorted(
                    snapshot.permissions,
                    key=lambda item: (item.action.value, item.scope.value),
                )
            ],
        }

    return router
