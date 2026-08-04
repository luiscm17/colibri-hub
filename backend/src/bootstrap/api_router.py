from collections.abc import Callable

from fastapi import APIRouter

from access.adapters.http_router import (
    GetCurrentAccessProvider,
    create_access_router,
)
from auth.adapters.http.router import AuthUseCaseProvider, create_auth_router
from warehouse.bales.adapters.http.router import UseCaseProvider
from warehouse.bales.ports.authorization import AuthorizationPort, IdentityResolver
from warehouse.adapters.http.router import create_router as create_warehouse_router


def create_api_router(
    use_case_provider: UseCaseProvider,
    identity_resolver: IdentityResolver,
    authorization_provider: Callable[..., AuthorizationPort],
    get_current_access_provider: GetCurrentAccessProvider,
    auth_use_case_provider: AuthUseCaseProvider | None = None,
) -> APIRouter:
    """Create the top-level API router with version prefix."""
    router = APIRouter(prefix="/api/v1")
    router.include_router(
        create_warehouse_router(
            use_case_provider, identity_resolver, authorization_provider
        )
    )
    router.include_router(
        create_access_router(identity_resolver, get_current_access_provider)
    )
    if auth_use_case_provider is not None:
        router.include_router(
            create_auth_router(identity_resolver, auth_use_case_provider)
        )
    return router
