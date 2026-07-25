from dataclasses import dataclass

from warehouse.bales.domain.domain_errors import InvalidBaleNumberError


@dataclass(frozen=True, slots=True)
class BaleNumber:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not normalized:
            raise InvalidBaleNumberError("Bale number cannot be empty.")
        if len(normalized) > 10:
            raise InvalidBaleNumberError("Bale number cannot exceed 10 characters.")
        object.__setattr__(self, "value", normalized)
