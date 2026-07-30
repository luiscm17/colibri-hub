from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RegisterRawMaterialBatchResult:
    """Result data for a completed batch registration.

    Contains only the batch summary fields — no per-bale detail.

    Attributes:
        raw_material_batch_id: Technical UUID of the registered batch.
        shipment_number: Business-visible shipment identifier.
        received_at: Business date of physical reception.
        provider_name: Raw-material provider name.
        bale_count: Number of bales persisted in this batch.
    """

    raw_material_batch_id: UUID
    shipment_number: str
    received_at: date
    provider_name: str
    bale_count: int
