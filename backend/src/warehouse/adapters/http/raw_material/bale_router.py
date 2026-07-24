from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, status

from warehouse.adapters.http.raw_material.bale_reception_mapping import (
    bale_reception_to_input,
    bale_reception_to_response,
)
from warehouse.adapters.http.raw_material.bale_reception_request import (
    BaleReceptionRequest,
)
from warehouse.adapters.http.raw_material.bale_reception_response import (
    BaleReceptionResponse,
)
from warehouse.application.raw_material.register_bale_reception import (
    RegisterBaleReception,
)
from warehouse.adapters.http.raw_material.error_response import ErrorResponse


UseCaseProvider = Callable[..., RegisterBaleReception]


def create_router(
    use_case_provider: UseCaseProvider,
) -> APIRouter:
    router = APIRouter(prefix="/bales")

    @router.post(
    "",
    response_model=BaleReceptionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "The shipment number is already registered."
            ),
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": (
                "The request or reception violates a validation rule."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected internal server error.",
        },
    },
)

    def register(
        request: BaleReceptionRequest,
        use_case: Annotated[RegisterBaleReception, Depends(use_case_provider)],
    ) -> BaleReceptionResponse:
        reception_input = bale_reception_to_input(request)
        result = use_case.execute(reception_input)
        return bale_reception_to_response(result)

    return router
