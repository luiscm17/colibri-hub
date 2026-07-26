from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ReceivedBaleCommand:
    """Input data for one bale within a raw-material batch registration.
    
    Attributes:
        bale_number: Business-visible bale number, unique within the batch.
        material_type: Raw-material classification.
        dtex: Technical linear-density value.
        gross_weight_kg: Gross bale weight including container.
        container_weight_kg: Container (tare) weight.
    """
    
    bale_number: str
    material_type: str
    dtex: Decimal
    gross_weight_kg: Decimal
    container_weight_kg: Decimal


@dataclass(frozen=True, slots=True)
class RegisterRawMaterialBatchCommand:
    """Input data to register a complete raw-material batch.
    
    Contains the batch header and all its bales. The registration receives
    one full shipment with one or more bales in a single transaction.
    
    Attributes:
        received_at: Business timestamp of the physical reception.
        shipment_number: Globally unique shipment identifier.
        provider_name: Raw-material provider name.
        bales: Tuple of individual bale input commands.
    """
    
    received_at: datetime
    shipment_number: str
    provider_name: str
    bales: tuple[ReceivedBaleCommand, ...]
