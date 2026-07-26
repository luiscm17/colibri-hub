from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from warehouse.bales.domain.domain_errors import InvalidDtexError


@dataclass(frozen=True, slots=True)
class Dtex:
    """Technical linear-density characteristic (DTEX).
    
    Represents the recorded linear-density value for a raw material bale, as
    defined in the yarn count catalog. Must be a positive finite decimal.
    
    Attributes:
        value: Linear-density value as a positive finite decimal.
    
    Raises:
        InvalidDtexError: If value is not a valid finite decimal or
            is less than or equal to zero.
    """
    
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
