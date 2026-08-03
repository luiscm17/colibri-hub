"""Port for authentication account persistence."""

from typing import Protocol

from auth.domain.account import AuthenticationAccount
from auth.domain.email import NormalizedEmail


class AccountRepository(Protocol):
    """Resolve and persist application-owned authentication account state."""

    def find_by_subject(self, identity_subject: str) -> AuthenticationAccount | None:
        """Resolve an account by its provider identity subject."""
        ...

    def find_by_email(self, email: NormalizedEmail) -> AuthenticationAccount | None:
        """Resolve an account by normalized email."""
        ...

    def find_by_id(self, account_id: str) -> AuthenticationAccount | None:
        """Resolve an account by its internal identifier."""
        ...

    def list_all(self) -> list[AuthenticationAccount]:
        """Return all accounts ordered by creation time."""
        ...

    def list_enabled_administrators(self) -> list[AuthenticationAccount]:
        """Return enabled accounts that hold System Administrator access."""
        ...

    def save(self, account: AuthenticationAccount) -> None:
        """Persist a new or updated account. Raises on constraint violation."""
        ...
