import logging
from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler

from warehouse.bales.adapters.http.error_handlers import (
    bale_not_found_handler,
    domain_error_handler,
    duplicate_bale_number_handler,
    duplicate_delivery_identity_handler,
    duplicate_shipment_number_handler,
    invalid_date_range_handler,
    invalid_status_filter_handler,
)
from warehouse.bales.adapters.http.error_mapping import (
    error_json_response,
)
from warehouse.bales.adapters.http.error_response import (
    FieldErrorResponse,
)
from warehouse.bales.application.errors import (
    BaleNotFoundError,
    DuplicateBaleNumberError,
    DuplicateDeliveryIdentityError,
    DuplicateShipmentNumberError,
    InvalidDateRangeError,
    InvalidStatusFilterError,
)
from warehouse.bales.domain.domain_errors import DomainError
from warehouse.bales.ports.authorization import AuthorizationDenied

from auth.domain.errors import AuthenticationError
from auth.adapters.http.error_handlers import authentication_error_handler


logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register HTTP exception handlers for domain and system errors.
    
    Maps application-layer and domain errors to structured JSON responses
    with appropriate HTTP status codes.
    
    Handlers are registered from most specific to least specific.
    FastAPI/Starlette matches handlers in registration order, so specific
    application errors must be registered before the generic DomainError
    catch-all.
    
    Args:
        app: The FastAPI application to register handlers on.
    """
    # Application-level errors (most specific first)
    app.add_exception_handler(
        DuplicateDeliveryIdentityError,
        cast(ExceptionHandler, duplicate_delivery_identity_handler),
    )
    app.add_exception_handler(
        BaleNotFoundError,
        cast(ExceptionHandler, bale_not_found_handler),
    )
    app.add_exception_handler(
        InvalidDateRangeError,
        cast(ExceptionHandler, invalid_date_range_handler),
    )
    app.add_exception_handler(
        InvalidStatusFilterError,
        cast(ExceptionHandler, invalid_status_filter_handler),
    )
    app.add_exception_handler(
        DuplicateShipmentNumberError,
        cast(ExceptionHandler, duplicate_shipment_number_handler),
    )
    app.add_exception_handler(
        DuplicateBaleNumberError,
        cast(ExceptionHandler, duplicate_bale_number_handler),
    )
    # Domain-level catch-all (less specific — catches InvalidReceptionDateError,
    # InvalidDeliveryDateError, ExcessiveBatchSizeError, and all other DomainError subclasses)
    app.add_exception_handler(
        DomainError,
        cast(ExceptionHandler, domain_error_handler),
    )
    app.add_exception_handler(
        AuthorizationDenied,
        cast(ExceptionHandler, authorization_denied_handler),
    )
    app.add_exception_handler(
        AuthenticationError,
        cast(ExceptionHandler, authentication_error_handler),
    )
    # Framework and generic handlers (least specific)
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


async def authorization_denied_handler(
    request: Request, error: AuthorizationDenied
) -> JSONResponse:
    """Return the same generic business denial for every Access failure."""
    del request, error
    return error_json_response(
        status_code=status.HTTP_403_FORBIDDEN,
        code="access_denied",
        message="Access is denied.",
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
