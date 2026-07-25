from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict


class _HttpResponseModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RegisteredBaleResponse(_HttpResponseModel):
    id: UUID
    bale_number: str
    material_type: str
    dtex: Decimal
    gross_weight_kg: Decimal
    container_weight_kg: Decimal
    status: Literal["in_warehouse"]


class BaleReceptionResponse(_HttpResponseModel):
    reception_id: UUID
    shipment_number: str
    received_at: AwareDatetime
    provider_name: str
    bale_count: int
    bales: tuple[RegisteredBaleResponse, ...]
