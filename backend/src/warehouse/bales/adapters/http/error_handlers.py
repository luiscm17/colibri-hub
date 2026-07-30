from fastapi import Request, status
from fastapi.responses import JSONResponse

from warehouse.bales.adapters.http.error_mapping import error_json_response
from warehouse.bales.adapters.http.error_response import FieldErrorResponse
from warehouse.bales.application.errors import (
    BaleNotFoundError,
    DuplicateBaleNumberError,
    DuplicateDeliveryIdentityError,
    DuplicateShipmentNumberError,
    InvalidDateRangeError,
    InvalidStatusFilterError,
)
from warehouse.bales.domain.domain_errors import DomainError


async def duplicate_shipment_number_handler(
    request: Request, error: DuplicateShipmentNumberError
) -> JSONResponse:
    """Handle duplicate shipment number errors (409 Conflict)."""
    del request
    return error_json_response(
        status_code=status.HTTP_409_CONFLICT,
        code="duplicate_shipment_number",
        message=str(error),
        fields=(FieldErrorResponse(path="shipment_number", message="The shipment number must be unique."),),
    )


async def duplicate_bale_number_handler(
    request: Request, error: DuplicateBaleNumberError
) -> JSONResponse:
    """Handle duplicate bale number errors (422 Unprocessable Content)."""
    del request
    return error_json_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="duplicate_bale_number",
        message=str(error),
        fields=(FieldErrorResponse(path="bales[].bale_number", message="Bale numbers must be unique."),),
    )


async def duplicate_delivery_identity_handler(
    request: Request, error: DuplicateDeliveryIdentityError
) -> JSONResponse:
    """Handle duplicate delivery identity errors (422 Unprocessable Content)."""
    del request
    return error_json_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="duplicate_delivery_identity",
        message=str(error),
        fields=(FieldErrorResponse(path="bales", message="Bale identities must be unique after normalization."),),
    )


async def bale_not_found_handler(
    request: Request, error: BaleNotFoundError
) -> JSONResponse:
    """Handle bale not found errors (404 Not Found)."""
    del request
    return error_json_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="bale_not_found",
        message=str(error),
    )


async def invalid_date_range_handler(
    request: Request, error: InvalidDateRangeError
) -> JSONResponse:
    """Handle invalid date range errors (422 Unprocessable Content)."""
    del request
    return error_json_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="request_validation_error",
        message=str(error),
        fields=(FieldErrorResponse(path="received_from", message="received_from must not be later than received_to."),),
    )


async def invalid_status_filter_handler(
    request: Request, error: InvalidStatusFilterError
) -> JSONResponse:
    """Handle invalid status filter errors (422 Unprocessable Content)."""
    del request
    return error_json_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="request_validation_error",
        message=str(error),
        fields=(FieldErrorResponse(path="status", message="Status must be 'in_warehouse' or 'delivered'."),),
    )


async def domain_error_handler(request: Request, error: DomainError) -> JSONResponse:
    """Handle domain validation errors (422 Unprocessable Content)."""
    del request
    return error_json_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="domain_validation_error",
        message=str(error),
    )
