from decimal import Decimal, InvalidOperation
from typing import Annotated, Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


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
        received_at: Business timestamp of physical reception.
        provider_name: Raw-material provider name.
        bales: One or more bales in this batch (must not be empty).
    """
    
    shipment_number: str
    received_at: AwareDatetime
    provider_name: str
    bales: Annotated[tuple[ReceivedBaleRequest, ...], Field(min_length=1)]
