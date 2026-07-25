from pydantic import BaseModel, ConfigDict


class _ErrorResponseModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class FieldErrorResponse(_ErrorResponseModel):
    path: str
    message: str


class ErrorDetailResponse(_ErrorResponseModel):
    code: str
    message: str
    fields: tuple[FieldErrorResponse, ...] = ()


class ErrorResponse(_ErrorResponseModel):
    error: ErrorDetailResponse
