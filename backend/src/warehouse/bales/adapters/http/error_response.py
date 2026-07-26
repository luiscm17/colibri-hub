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
