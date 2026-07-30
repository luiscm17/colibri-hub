from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class _HttpResponseModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class BaleDetailResponse(_HttpResponseModel):
    """HTTP response model for the individual bale detail endpoint.

    Returns the full attributes of a single bale identified by its
    composite business identity (shipment_number + bale_number).

    Attributes:
        id: Technical UUID of the bale.
        shipment_number: Business-visible shipment identifier.
        bale_number: Bale identifier within the shipment.
        received_at: Business date of physical reception (ISO YYYY-MM-DD).
        provider_name: Raw-material provider name.
        material_type: Type of raw material.
        dtex: Linear density measurement.
        gross_weight_kg: Total weight including container.
        container_weight_kg: Weight of the container alone.
        net_weight_kg: Computed as gross_weight_kg minus container_weight_kg.
        status: Current bale lifecycle state.
        delivery_date: ISO date when delivered, None when in_warehouse.
    """

    id: UUID
    shipment_number: str
    bale_number: str
    received_at: str
    provider_name: str
    material_type: str
    dtex: Decimal
    gross_weight_kg: Decimal
    container_weight_kg: Decimal
    net_weight_kg: Decimal
    status: str
    delivery_date: str | None
