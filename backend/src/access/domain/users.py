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
