from fastapi.responses import JSONResponse

from warehouse.bales.adapters.http.error_response import (
    ErrorDetailResponse,
    ErrorResponse,
    FieldErrorResponse,
)


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
    return JSONResponse(status_code=status_code, content=response.model_dump(mode="json"))
