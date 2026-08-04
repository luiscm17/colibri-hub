"""Scope value object, Scope entity, and ScopeDefinition catalog entry.

Scope codes use exact-match semantics per tech spec §6.2.
Dot-separated segments are naming structure only — no inheritance.
"""

from dataclasses import dataclass
from datetime import datetime

from access.domain.actions import Action


@dataclass(frozen=True, slots=True)
class ScopeCode:
    """Immutable value object wrapping a validated scope code string."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or self.value != self.value.strip():
            raise ValueError("Scope code must be non-empty and normalized.")


@dataclass(slots=True)
class Scope:
    """A registered scope instance in the access system."""

    scope_id: str
    definition_key: str
    scope_code: str
    scope_name: str
    owning_context: str
    description: str
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ScopeDefinition:
    """Immutable scope definition from the recognized catalog.

    Catalog entries are product-versioned and not editable via admin requests.
    """

    definition_key: str
    scope_code: str
    scope_name: str
    owning_context: str
    description: str
    supported_actions: frozenset[Action]
