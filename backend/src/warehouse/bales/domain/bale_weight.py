from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from warehouse.bales.domain.domain_errors import InvalidBaleWeightError


@dataclass(frozen=True, slots=True)
class BaleWeight:
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
