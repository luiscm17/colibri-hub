from dataclasses import dataclass

from warehouse.bales.domain.domain_errors import InvalidMaterialTypeError


@dataclass(frozen=True, slots=True)
class MaterialType:
    """Raw-material classification for bales.
    
    Represents the recorded material classification for a raw material bale,
    such as fiber type or composition. Material types are normalized to uppercase
    and stripped of whitespace.
    
    Attributes:
        value: Normalized material type code (uppercase, stripped whitespace).
    
    Raises:
        InvalidMaterialTypeError: If the material type is empty or exceeds
            the 20 character limit after normalization.
    """
    
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not normalized:
            raise InvalidMaterialTypeError("Material Type cannot be empty.")
        if len(normalized) > 20:
            raise InvalidMaterialTypeError("Material Type cannot exceed 20 characters.")
        object.__setattr__(self, "value", normalized)
