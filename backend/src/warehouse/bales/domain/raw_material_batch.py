from dataclasses import dataclass

from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.domain_errors import (
    DuplicateBaleIdError,
    EmptyRawMaterialBatchError,
    InvalidProviderNameError,
)
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId
from warehouse.bales.domain.reception_datetime import ReceptionDateTime
from warehouse.bales.domain.shipment_number import ShipmentNumber


@dataclass(frozen=True, slots=True, eq=False)
class RawMaterialBatch:
    """A supplier-shipment grouping containing one or more raw-material bales.
    
    Represents a complete raw-material batch identified by a globally unique
    shipment number. A batch groups one or more bales received from a provider,
    along with their shared evidence or characteristics. It is not a production lot.
    
    Attributes:
        id: Technical identity for the raw material batch.
        received_at: Timestamp when the batch was received.
        shipment_number: Business-visible identifier, globally unique.
        provider_name: Provider name (stripped of whitespace, must be non-empty).
        bale_ids: Collection of Bale identities belonging to this batch.
    """
    
    id: RawMaterialBatchId
    received_at: ReceptionDateTime
    shipment_number: ShipmentNumber
    provider_name: str
    bale_ids: tuple[BaleId, ...]

    def __post_init__(self) -> None:
        provider_name = self.provider_name.strip()
        bale_ids = tuple(self.bale_ids)
        if not provider_name:
            raise InvalidProviderNameError("Provider name cannot be empty.")
        if not bale_ids:
            raise EmptyRawMaterialBatchError("Raw material reception must contain at least one bale.")
        if len(bale_ids) != len(set(bale_ids)):
            raise DuplicateBaleIdError("Raw material reception cannot contain duplicate bale IDs.")
        object.__setattr__(self, "provider_name", provider_name)
        object.__setattr__(self, "bale_ids", bale_ids)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RawMaterialBatch) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def bale_count(self) -> int:
        return len(self.bale_ids)
