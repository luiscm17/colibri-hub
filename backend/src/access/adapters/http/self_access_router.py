"""Self-access HTTP router: /access/me for the authenticated user."""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends
from shared.identity import AuthenticatedIdentity, IdentityResolver

from access.adapters.http.models import (
    AuthorizationResponse,
    CurrentAccessResponse,
    PermissionResponse,
    RoleSummaryResponse,
)
from access.application.get_current_access import GetCurrentAccess
from access.domain.actions import Action
from access.domain.errors import AccessProfileNotFound, AccessUserInactive

# Type alias for dependency provider
GetCurrentAccessProvider = Callable[..., GetCurrentAccess]


def create_self_access_router(
    identity_resolver: IdentityResolver,
    get_current_access_provider: GetCurrentAccessProvider,
) -> APIRouter:
    """Self-access router: /access/me for the authenticated user."""
    router = APIRouter(prefix="/access")

    @router.get("/me")
    def current_access(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_case: Annotated[GetCurrentAccess, Depends(get_current_access_provider)],
    ) -> CurrentAccessResponse:
        try:
            result = use_case.execute(subject=identity.subject)
        except AccessProfileNotFound:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile_not_found")
        except AccessUserInactive:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="profile_inactive")

        roles = [
            RoleSummaryResponse(role_id=r.role_id, code=r.code, name=r.name)
            for r in result.roles
        ]

        if result.is_global:
            return CurrentAccessResponse(
                user_id=result.user_id,
                user_code=result.user_code,
                display_name=result.display_name,
                is_active=result.is_active,
                roles=roles,
                authorization=AuthorizationResponse(
                    is_global=True,
                    actions=sorted(a.value for a in Action),
                    permissions=[],
                    version=result.authorization_version,
                ),
            )

        return CurrentAccessResponse(
            user_id=result.user_id,
            user_code=result.user_code,
            display_name=result.display_name,
            is_active=result.is_active,
            roles=roles,
            authorization=AuthorizationResponse(
                is_global=False,
                permissions=[
                    PermissionResponse(action=p.action, scope_code=p.scope_code)
                    for p in result.permissions
                ],
                version=result.authorization_version,
            ),
        )

    return router
