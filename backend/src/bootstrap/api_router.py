from collections.abc import Callable

from fastapi import APIRouter

from access.adapters.http_router import (
    AccessApplicationProvider,
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
    access_application_provider: AccessApplicationProvider,
    auth_use_case_provider: AuthUseCaseProvider | None = None,
) -> APIRouter:
    """Create the top-level API router with version prefix.
    
    Args:
        use_case_provider: FastAPI dependency for resolving use cases.
        identity_resolver: Resolves authenticated identity from request.
        authorization_provider: Resolves authorization port for warehouse.
        access_application_provider: Resolves access application service.
        auth_use_case_provider: Resolves auth use cases (optional for tests).
    
    Returns:
        Configured APIRouter under /api/v1.
    """
    router = APIRouter(prefix="/api/v1")
    router.include_router(
        create_warehouse_router(
            use_case_provider, identity_resolver, authorization_provider
        )
    )
    router.include_router(
        create_access_router(identity_resolver, access_application_provider)
    )
    if auth_use_case_provider is not None:
        router.include_router(
            create_auth_router(identity_resolver, auth_use_case_provider)
        )
    return router
