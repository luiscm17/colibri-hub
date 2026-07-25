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
    response = ErrorResponse(
        error=ErrorDetailResponse(code=code, message=message, fields=fields)
    )
    return JSONResponse(status_code=status_code, content=response.model_dump(mode="json"))
