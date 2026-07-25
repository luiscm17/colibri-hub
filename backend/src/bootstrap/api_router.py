from fastapi import APIRouter

from warehouse.bales.adapters.http.router import UseCaseProvider
from warehouse.adapters.http.router import create_router as create_warehouse_router


def create_api_router(use_case_provider: UseCaseProvider) -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(create_warehouse_router(use_case_provider))
    return router
