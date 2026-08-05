"""Supported access control actions and Permission value object.

Actions describe business intent, not HTTP methods or UI interactions.
"""

from dataclasses import dataclass
from enum import StrEnum


class Action(StrEnum):
    """Stable action values for authorization evaluation."""

    READ = "read"
    WRITE = "write"
    EDIT = "edit"
    EDIT_OUTSIDE_WINDOW = "edit_outside_window"
    MANAGE_ACCESS = "manage_access"


PRIVILEGED_ACTIONS: frozenset[Action] = frozenset({
    Action.MANAGE_ACCESS,
    Action.EDIT_OUTSIDE_WINDOW,
})
"""Actions that only the System Administrator role may grant."""


@dataclass(frozen=True, slots=True)
class Permission:
    """An exact (action, scope_code) authorization grant."""

    action: Action
    scope_code: str

    def __post_init__(self) -> None:
        if not self.scope_code or self.scope_code != self.scope_code.strip():
            raise ValueError("Permission scope_code must be non-empty and trimmed.")
