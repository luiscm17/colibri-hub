from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RawMaterialBatchId:
    """Unique identifier for a raw material batch.
    
    Attributes:
        value: UUID that uniquely identifies the raw material batch.
    """
    
    value: UUID
