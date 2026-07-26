from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BaleId:
    """Unique identifier for a bale.
    
    Attributes:
        value: UUID that uniquely identifies the bale.
    """
    
    value: UUID
