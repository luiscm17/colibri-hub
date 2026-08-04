"""Top-level API router composition under /api/v1."""

from collections.abc import Callable

from fastapi import APIRouter

from access.adapters.http.router import (
    AdminUseCaseProvider,
    GetCurrentAccessProvider,
    create_admin_router,
    create_self_access_router,
)
from auth.adapters.http.router import AuthUseCaseProvider, create_auth_router
from warehouse.bales.adapters.http.router import UseCaseProvider
from warehouse.bales.ports.authorization import AuthorizationPort, IdentityResolver

from access.application.authorize_action import AuthorizeAction


def create_api_router(
    use_case_provider: UseCaseProvider,
    identity_resolver: IdentityResolver,
    authorization_provider: Callable[..., AuthorizationPort],
    get_current_access_provider: GetCurrentAccessProvider,
    authorize_action_provider: Callable[..., AuthorizeAction],
    admin_use_case_provider: AdminUseCaseProvider | None = None,
    auth_use_case_provider: AuthUseCaseProvider | None = None,
) -> APIRouter:
    """Create the top-level API router with version prefix."""
    from warehouse.adapters.http.router import create_router as create_warehouse_router

    router = APIRouter(prefix="/api/v1")
    router.include_router(
        create_warehouse_router(
            use_case_provider, identity_resolver, authorization_provider
        )
    )
    router.include_router(
        create_self_access_router(identity_resolver, get_current_access_provider)
    )
    if admin_use_case_provider is not None:
        router.include_router(
            create_admin_router(
                identity_resolver, authorize_action_provider, admin_use_case_provider
            )
        )
    if auth_use_case_provider is not None:
        router.include_router(
            create_auth_router(identity_resolver, auth_use_case_provider)
        )
    return router
