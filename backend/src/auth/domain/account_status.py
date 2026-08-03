from enum import StrEnum


class AuthenticationAccountStatus(StrEnum):
    """Authentication account lifecycle states.

    Governs which operations are available to the identity:
    - AWAITING_PASSWORD_CHANGE: may only replace provisional password, inspect state, or log out.
    - ACTIVE: may proceed to Access Control for protected operations.
    - DISABLED: denied regardless of token validity.
    """

    AWAITING_PASSWORD_CHANGE = "awaiting_password_change"
    ACTIVE = "active"
    DISABLED = "disabled"
