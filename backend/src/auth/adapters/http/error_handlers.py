"""Authentication-specific HTTP error handlers."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from infra.http.error_envelope import error_json_response

from auth.domain.errors import AuthenticationError

_ERROR_STATUS_MAP: dict[str, int] = {
    "authentication_required": status.HTTP_401_UNAUTHORIZED,
    "authentication_failed": status.HTTP_401_UNAUTHORIZED,
    "current_password_rejected": status.HTTP_401_UNAUTHORIZED,
    "password_change_required": status.HTTP_403_FORBIDDEN,
    "authentication_account_not_found": status.HTTP_404_NOT_FOUND,
    "duplicate_authentication_email": status.HTTP_409_CONFLICT,
    "authentication_version_conflict": status.HTTP_409_CONFLICT,
    "administrator_continuity_required": status.HTTP_409_CONFLICT,
    "authentication_account_state_conflict": status.HTTP_409_CONFLICT,
    "authentication_identity_conflict": status.HTTP_409_CONFLICT,
    "replacement_password_must_differ": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "weak_password": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "authentication_change_reason_required": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "authentication_provider_unavailable": status.HTTP_503_SERVICE_UNAVAILABLE,
}


async def authentication_error_handler(
    request: Request, error: AuthenticationError
) -> JSONResponse:
    """Map any AuthenticationError to the shared error envelope."""
    del request
    status_code = _ERROR_STATUS_MAP.get(
        error.code, status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    return error_json_response(
        status_code=status_code,
        code=error.code,
        message=str(error),
    )
