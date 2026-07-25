from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ReceivedBaleCommand:
    bale_number: str
    material_type: str
    dtex: Decimal
    gross_weight_kg: Decimal
    container_weight_kg: Decimal


@dataclass(frozen=True, slots=True)
class RegisterRawMaterialBatchCommand:
    received_at: datetime
    shipment_number: str
    provider_name: str
    bales: tuple[ReceivedBaleCommand, ...]
