import logging
from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler

from warehouse.bales.adapters.http.error_handlers import (
    domain_error_handler,
    duplicate_bale_number_handler,
    duplicate_shipment_number_handler,
)
from warehouse.bales.adapters.http.error_mapping import (
    error_json_response,
)
from warehouse.bales.adapters.http.error_response import (
    FieldErrorResponse,
)
from warehouse.bales.application.errors import (
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
)
from warehouse.bales.domain.domain_errors import DomainError


logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register HTTP exception handlers for domain and system errors.
    
    Maps application-layer and domain errors to structured JSON responses
    with appropriate HTTP status codes.
    
    Args:
        app: The FastAPI application to register handlers on.
    """
    app.add_exception_handler(
        DuplicateShipmentNumberError,
        cast(ExceptionHandler, duplicate_shipment_number_handler),
    )
    app.add_exception_handler(
        DuplicateBaleNumberError,
        cast(ExceptionHandler, duplicate_bale_number_handler),
    )
    app.add_exception_handler(
        DomainError,
        cast(ExceptionHandler, domain_error_handler),
    )
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, request_validation_error_handler),
    )
    app.add_exception_handler(
        Exception,
        cast(ExceptionHandler, unexpected_error_handler),
    )


async def request_validation_error_handler(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic request validation errors (422 Unprocessable Content).
    
    Translates each validation error item into a structured field error
    with the JSON path and error message.
    """
    del request

    fields = tuple(
        FieldErrorResponse(
            path=_validation_error_path(item.get("loc", ())),
            message=str(item.get("msg", "Invalid value.")),
        )
        for item in error.errors()
    )

    return error_json_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="request_validation_error",
        message="The request is invalid.",
        fields=fields,
    )


async def unexpected_error_handler(
    request: Request,
    error: Exception,
) -> JSONResponse:
    """Handle unexpected errors (500 Internal Server Error).
    
    Logs the full exception with request context and returns a generic
    error response without exposing implementation details.
    """
    logger.exception(
        "Unhandled error while processing HTTP request",
        extra={
            "http_method": request.method,
            "http_path": request.url.path,
        },
        exc_info=error,
    )

    return error_json_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_server_error",
        message="An unexpected internal error occurred.",
    )


def _validation_error_path(location: tuple[object, ...]) -> str:
    """Convert a Pydantic error location tuple to a dot-separated JSON path."""
    parts = tuple(str(part) for part in location if part != "body")
    return ".".join(parts) or "body"
