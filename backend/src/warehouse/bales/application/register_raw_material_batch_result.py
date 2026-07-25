from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RegisteredBaleResult:
    id: UUID
    bale_number: str
    material_type: str
    dtex: Decimal
    gross_weight_kg: Decimal
    container_weight_kg: Decimal
    status: str


@dataclass(frozen=True, slots=True)
class RegisterRawMaterialBatchResult:
    reception_id: UUID
    shipment_number: str
    received_at: datetime
    provider_name: str
    bale_count: int
    bales: tuple[RegisteredBaleResult, ...]
