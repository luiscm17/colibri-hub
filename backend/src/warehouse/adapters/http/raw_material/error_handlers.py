from fastapi import Request, status
from fastapi.responses import JSONResponse

from warehouse.adapters.http.raw_material.error_mapping import (
    error_json_response,
)
from warehouse.adapters.http.raw_material.error_response import (
    FieldErrorResponse,
)
from warehouse.application.raw_material.bale_reception_errors import (
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
)
from warehouse.domain.raw_material.domain_errors import DomainError


async def duplicate_shipment_number_handler(
    request: Request,
    error: DuplicateShipmentNumberError,
) -> JSONResponse:
    del request

    return error_json_response(
        status_code=status.HTTP_409_CONFLICT,
        code="duplicate_shipment_number",
        message=str(error),
        fields=(
            FieldErrorResponse(
                path="shipment_number",
                message="The shipment number must be unique.",
            ),
        ),
    )


async def duplicate_bale_number_handler(
    request: Request,
    error: DuplicateBaleNumberError,
) -> JSONResponse:
    del request

    return error_json_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="duplicate_bale_number",
        message=str(error),
        fields=(
            FieldErrorResponse(
                path="bales[].bale_number",
                message="Bale numbers must be unique.",
            ),
        ),
    )


async def domain_error_handler(
    request: Request,
    error: DomainError,
) -> JSONResponse:
    del request

    return error_json_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="domain_validation_error",
        message=str(error),
    )