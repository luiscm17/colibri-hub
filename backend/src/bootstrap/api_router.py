from collections.abc import Callable

from fastapi import APIRouter

from access.adapters.http_router import (
    AccessApplicationProvider,
    create_access_router,
)
from warehouse.bales.adapters.http.router import UseCaseProvider
from warehouse.bales.ports.authorization import AuthorizationPort, IdentityResolver
from warehouse.adapters.http.router import create_router as create_warehouse_router


def create_api_router(
    use_case_provider: UseCaseProvider,
    identity_resolver: IdentityResolver,
    authorization_provider: Callable[..., AuthorizationPort],
    access_application_provider: AccessApplicationProvider,
) -> APIRouter:
    """Create the top-level API router with version prefix.
    
    Args:
        use_case_provider: FastAPI dependency for resolving use cases.
    
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
    return router
