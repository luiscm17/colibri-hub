import re
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class _HttpRequestModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class BaleIdentityRequest(_HttpRequestModel):
    """Identifies a single bale by its business identity for delivery.

    Attributes:
        shipment_number: Shipment the bale belongs to.
        bale_number: Business-visible bale number within the shipment.
    """

    shipment_number: str
    bale_number: str


class DeliverBalesRequest(_HttpRequestModel):
    """HTTP request model for batch delivery of bales.

    Attributes:
        delivery_date: Business date of physical delivery (ISO format YYYY-MM-DD).
        bales: One to fifty bale identities to deliver.
    """

    delivery_date: str
    bales: Annotated[
        tuple[BaleIdentityRequest, ...], Field(min_length=1, max_length=50)
    ]

    @field_validator("delivery_date")
    @classmethod
    def validate_delivery_date(cls, value: str) -> str:
        if not _DATE_REGEX.match(value):
            raise ValueError(
                "delivery_date must be a valid ISO date in YYYY-MM-DD format."
            )
        try:
            date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(
                "delivery_date must be a valid calendar date."
            ) from error
        return value
