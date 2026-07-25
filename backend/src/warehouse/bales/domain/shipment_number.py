from dataclasses import dataclass

from warehouse.bales.domain.domain_errors import InvalidShipmentNumberError


@dataclass(frozen=True, slots=True)
class ShipmentNumber:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not normalized:
            raise InvalidShipmentNumberError("Shipment number cannot be empty.")
        if len(normalized) > 10:
            raise InvalidShipmentNumberError("Shipment number cannot exceed 10 characters.")
        object.__setattr__(self, "value", normalized)
