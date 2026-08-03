"""Shared error envelope for all HTTP responses across bounded contexts."""

from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict


class _ErrorResponseModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class FieldErrorResponse(_ErrorResponseModel):
    """A single field-level validation error.

    Attributes:
        path: JSON path to the field that caused the error.
        message: Human-readable description of the error.
    """

    path: str
    message: str


class ErrorDetailResponse(_ErrorResponseModel):
    """Error detail envelope containing the error code and message.

    Attributes:
        code: Machine-readable error code.
        message: Human-readable error summary.
        fields: Optional per-field error details.
    """

    code: str
    message: str
    fields: tuple[FieldErrorResponse, ...] = ()


class ErrorResponse(_ErrorResponseModel):
    """Standard error response envelope.

    Attributes:
        error: The error detail containing code, message, and field errors.
    """

    error: ErrorDetailResponse


def error_json_response(
    *,
    status_code: int,
    code: str,
    message: str,
    fields: tuple[FieldErrorResponse, ...] = (),
) -> JSONResponse:
    """Build a JSON error response with the standard envelope.

    Args:
        status_code: HTTP status code for the response.
        code: Machine-readable error code.
        message: Human-readable error message.
        fields: Optional per-field error details.

    Returns:
        A FastAPI JSONResponse with the error envelope.
    """
    response = ErrorResponse(
        error=ErrorDetailResponse(code=code, message=message, fields=fields)
    )
    return JSONResponse(
        status_code=status_code, content=response.model_dump(mode="json")
    )
