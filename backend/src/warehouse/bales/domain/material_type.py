from dataclasses import dataclass

from warehouse.bales.domain.domain_errors import InvalidMaterialTypeError


@dataclass(frozen=True, slots=True)
class MaterialType:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not normalized:
            raise InvalidMaterialTypeError("Material Type cannot be empty.")
        if len(normalized) > 20:
            raise InvalidMaterialTypeError("Material Type cannot exceed 20 characters.")
        object.__setattr__(self, "value", normalized)
