from dataclasses import dataclass

from warehouse.bales.domain.domain_errors import InvalidShipmentNumberError


@dataclass(frozen=True, slots=True)
class ShipmentNumber:
    """Business-visible identifier of a raw-material batch.
    
    The shipment number is a globally unique identifier for a raw-material batch.
    It is normalized to uppercase and stripped of whitespace. Shipment numbers
    are limited to 10 characters.
    
    Attributes:
        value: Shipment number string (max 10 characters after normalization).
    
    Raises:
        InvalidShipmentNumberError: If the shipment number is empty or exceeds
            the 10 character limit after normalization.
    """
    
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not normalized:
            raise InvalidShipmentNumberError("Shipment number cannot be empty.")
        if len(normalized) > 10:
            raise InvalidShipmentNumberError("Shipment number cannot exceed 10 characters.")
        object.__setattr__(self, "value", normalized)
