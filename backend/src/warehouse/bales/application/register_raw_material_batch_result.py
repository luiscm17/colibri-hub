from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RegisteredBaleResult:
    """Result data for one registered bale.
    
    Attributes:
        id: Technical UUID of the registered bale.
        bale_number: Business-visible bale number.
        material_type: Recorded material classification.
        dtex: Technical linear-density value.
        gross_weight_kg: Gross weight including container.
        container_weight_kg: Container (tare) weight.
        status: Initial custody state (always "in_warehouse").
    """
    
    id: UUID
    bale_number: str
    material_type: str
    dtex: Decimal
    gross_weight_kg: Decimal
    container_weight_kg: Decimal
    status: str


@dataclass(frozen=True, slots=True)
class RegisterRawMaterialBatchResult:
    """Result data for a completed batch registration.
    
    Attributes:
        raw_material_batch_id: Technical UUID of the registered batch.
        shipment_number: Business-visible shipment identifier.
        received_at: Business timestamp of physical reception.
        provider_name: Raw-material provider name.
        bale_count: Number of bales in this batch.
        bales: Tuple of per-bale registration results.
    """
    
    raw_material_batch_id: UUID
    shipment_number: str
    received_at: datetime
    provider_name: str
    bale_count: int
    bales: tuple[RegisteredBaleResult, ...]
