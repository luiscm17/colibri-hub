"""Access Control HTTP error handlers."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from infra.http.error_envelope import error_json_response

from access.domain.errors import AccessError

_ERROR_STATUS_MAP: dict[str, int] = {
    # 403
    "access_denied": status.HTTP_403_FORBIDDEN,
    "access_user_inactive": status.HTTP_403_FORBIDDEN,
    "access_profile_not_found": status.HTTP_403_FORBIDDEN,
    # 404
    "access_user_not_found": status.HTTP_404_NOT_FOUND,
    "access_role_not_found": status.HTTP_404_NOT_FOUND,
    "access_scope_not_found": status.HTTP_404_NOT_FOUND,
    "access_preset_not_found": status.HTTP_404_NOT_FOUND,
    # 409
    "duplicate_access_identity": status.HTTP_409_CONFLICT,
    "duplicate_access_user_code": status.HTTP_409_CONFLICT,
    "duplicate_access_role_code": status.HTTP_409_CONFLICT,
    "duplicate_access_preset_code": status.HTTP_409_CONFLICT,
    "duplicate_access_scope_code": status.HTTP_409_CONFLICT,
    "access_version_conflict": status.HTTP_409_CONFLICT,
    "administrator_continuity_required": status.HTTP_409_CONFLICT,
    "inactive_access_role": status.HTTP_409_CONFLICT,
    "inactive_access_scope": status.HTTP_409_CONFLICT,
    # 422
    "invalid_access_action": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "unsupported_action_for_scope": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "unrecognized_scope_definition": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "privileged_action_requires_system_administrator": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "duplicate_role_permission": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "access_change_reason_required": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "reserved_role_mutation_forbidden": status.HTTP_422_UNPROCESSABLE_CONTENT,
}


async def access_error_handler(request: Request, error: AccessError) -> JSONResponse:
    """Map any AccessError to the shared error envelope."""
    del request
    status_code = _ERROR_STATUS_MAP.get(
        error.code, status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    return error_json_response(
        status_code=status_code,
        code=error.code,
        message=str(error),
    )
