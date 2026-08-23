"""Port for verified self-service mandatory password replacement."""

from typing import Protocol


class PasswordReplacementPort(Protocol):
    """Replace a required password against the authenticated provider session."""

    def replace_required_password(
        self,
        *,
        subject: str,
        session_id: str | None,
        current_password: str,
        new_password: str,
    ) -> None:
        """Verify, replace, then terminate the authenticated provider session."""
        ...
