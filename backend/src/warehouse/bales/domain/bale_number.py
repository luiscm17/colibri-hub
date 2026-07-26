from dataclasses import dataclass

from warehouse.bales.domain.domain_errors import InvalidBaleNumberError


@dataclass(frozen=True, slots=True)
class BaleNumber:
    """Business-visible number identifying a bale within its raw-material batch.
    
    A bale number is unique within its batch, but may repeat across different
    batches. The full business identity is `shipment_number` + `bale_number`.
    Bale numbers are normalized to uppercase and stripped of whitespace.
    
    Attributes:
        value: Bale number string (max 10 characters after normalization).
    
    Raises:
        InvalidBaleNumberError: If the bale number is empty or exceeds
            the 10 character limit after normalization.
    """
    
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not normalized:
            raise InvalidBaleNumberError("Bale number cannot be empty.")
        if len(normalized) > 10:
            raise InvalidBaleNumberError("Bale number cannot exceed 10 characters.")
        object.__setattr__(self, "value", normalized)
