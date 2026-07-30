import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class _HttpRequestModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ReceivedBaleRequest(_HttpRequestModel):
    """HTTP request model for one bale in a reception payload.
    
    Attributes:
        bale_number: Business-visible bale number.
        material_type: Raw-material classification.
        dtex: Technical linear-density value.
        gross_weight_kg: Gross weight including container.
        container_weight_kg: Container (tare) weight.
    """
    
    bale_number: str
    material_type: str
    dtex: Decimal
    gross_weight_kg: Decimal
    container_weight_kg: Decimal

    @field_validator(
        "dtex", "gross_weight_kg", "container_weight_kg", mode="before"
    )
    @classmethod
    def finite_decimal(cls, value: Any) -> Decimal:
        if not isinstance(value, str):
            raise ValueError("Decimal values must be provided as JSON strings.")
        try:
            decimal_value = Decimal(value)
        except InvalidOperation as error:
            raise ValueError("Value must be a valid decimal string.") from error
        if not decimal_value.is_finite():
            raise ValueError("Decimal value must be finite.")
        return decimal_value


class BaleReceptionRequest(_HttpRequestModel):
    """HTTP request model for registering a complete raw-material batch.
    
    Attributes:
        shipment_number: Globally unique shipment identifier.
        received_at: Business date of physical reception (ISO format YYYY-MM-DD).
        provider_name: Raw-material provider name.
        bales: One or more bales in this batch (1–100).
    """
    
    shipment_number: str
    received_at: str
    provider_name: str
    bales: Annotated[
        tuple[ReceivedBaleRequest, ...], Field(min_length=1, max_length=100)
    ]

    @field_validator("received_at")
    @classmethod
    def validate_received_at(cls, value: str) -> str:
        if not _DATE_REGEX.match(value):
            raise ValueError(
                "received_at must be a valid ISO date in YYYY-MM-DD format."
            )
        try:
            date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(
                "received_at must be a valid calendar date."
            ) from error
        return value
