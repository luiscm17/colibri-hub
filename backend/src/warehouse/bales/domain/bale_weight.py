from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from warehouse.bales.domain.domain_errors import InvalidBaleWeightError


@dataclass(frozen=True, slots=True)
class BaleWeight:
    """Weight measurements for a raw material bale.
    
    Captures gross weight and container (tare) weight in kilograms, from which
    the net weight is calculated. The gross weight must exceed the container
    weight, and both must be finite positive decimals.
    
    Attributes:
        gross_kg: Gross bale weight including container in kilograms.
        container_kg: Container (tare) weight in kilograms.
    
    Properties:
        net_kg: Calculated net weight (gross minus container) in kilograms.
    
    Raises:
        InvalidBaleWeightError: If gross or container weights are invalid
            (not finite decimals, zero or negative, or if gross <= container).
    """
    
    gross_kg: Decimal
    container_kg: Decimal

    def __post_init__(self) -> None:
        gross = self._normalize(self.gross_kg, "Gross Weight")
        container = self._normalize(self.container_kg, "Container Weight")
        if gross <= Decimal("0"):
            raise InvalidBaleWeightError("Gross weight must be greater than zero.")
        if container <= Decimal("0"):
            raise InvalidBaleWeightError("Container weight must be greater than zero.")
        if gross <= container:
            raise InvalidBaleWeightError("Gross weight must exceed container weight.")
        object.__setattr__(self, "gross_kg", gross)
        object.__setattr__(self, "container_kg", container)

    @property
    def net_kg(self) -> Decimal:
        return self.gross_kg - self.container_kg

    @staticmethod
    def _normalize(value: Decimal, field_name: str) -> Decimal:
        try:
            normalized = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise InvalidBaleWeightError(f"{field_name} must be a valid decimal value.")
        if not normalized.is_finite():
            raise InvalidBaleWeightError(f"{field_name} must be finite.")
        return normalized
