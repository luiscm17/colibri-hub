"""AccessUser entity."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AccessUser:
    """An access-controlled user profile linked to an external identity."""

    user_id: str
    identity_subject: str
    user_code: str
    display_name: str
    is_active: bool
    authorization_version: int
    version: int
    created_at: datetime
    updated_at: datetime

    def deactivate(self, *, at: datetime) -> None:
        """Deactivate the user profile. Idempotent when already inactive."""
        if not self.is_active:
            return
        self.is_active = False
        self.version += 1
        self.updated_at = at

    def activate(self, *, at: datetime) -> None:
        """Reactivate the user profile. Idempotent when already active."""
        if self.is_active:
            return
        self.is_active = True
        self.version += 1
        self.updated_at = at
