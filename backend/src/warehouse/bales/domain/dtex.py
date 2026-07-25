from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from warehouse.bales.domain.domain_errors import InvalidDtexError


@dataclass(frozen=True, slots=True)
class Dtex:
    value: Decimal

    def __post_init__(self) -> None:
        try:
            normalized = Decimal(str(self.value))
        except (InvalidOperation, ValueError, TypeError) as error:
            raise InvalidDtexError(f"{self.value} must be a valid decimal value.") from error
        if not normalized.is_finite():
            raise InvalidDtexError(f"{self.value} must be finite.")
        if normalized <= Decimal("0"):
            raise InvalidDtexError("Dtex must be greater than zero.")
        object.__setattr__(self, "value", normalized)
