from fastapi import APIRouter

from warehouse.bales.adapters.http.router import (
    UseCaseProvider,
    create_router as create_bale_router,
)


def create_router(use_case_provider: UseCaseProvider) -> APIRouter:
    router = APIRouter(prefix="/warehouse")
    router.include_router(create_bale_router(use_case_provider))
    return router
