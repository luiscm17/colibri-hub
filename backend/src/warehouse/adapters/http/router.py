from collections.abc import Callable

from fastapi import APIRouter

from warehouse.bales.adapters.http.router import (
    UseCaseProvider,
    create_router as create_bale_router,
)
from warehouse.bales.ports.authorization import AuthorizationPort, IdentityResolver


def create_router(
    use_case_provider: UseCaseProvider,
    identity_resolver: IdentityResolver,
    authorization_provider: Callable[..., AuthorizationPort],
) -> APIRouter:
    """Create the top-level Warehouse HTTP router.
    
    Composes all warehouse sub-domain routers under the /warehouse prefix.
    
    Args:
        use_case_provider: FastAPI dependency for resolving the bale use case.
    
    Returns:
        Configured APIRouter with warehouse sub-routes.
    """
    router = APIRouter(prefix="/warehouse")
    router.include_router(
        create_bale_router(
            use_case_provider, identity_resolver, authorization_provider
        )
    )
    return router
