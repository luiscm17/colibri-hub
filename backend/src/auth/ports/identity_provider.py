"""Port for the external identity provider.

Provider-specific request/response types do NOT cross this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True, slots=True)
class ProviderIdentity:
    """Result of creating or resolving a provider identity."""

    subject: str
    email: str


@dataclass(frozen=True, slots=True)
class ProviderLoginAuditEvidence:
    """Safe, provider-neutral evidence of a successful password login."""

    entry_id: str
    occurred_at: str
    subject: str | None
    event_type: Literal["login_succeeded"]


class IdentityProviderPort(Protocol):
    """Create identities, update credentials, ban/unban users, revoke sessions.

    All methods operate server-side using administrative credentials.
    """

    def create_user(self, *, email: str, password: str) -> ProviderIdentity:
        """Create a provider identity without sending email confirmation."""
        ...

    def update_password(self, *, subject: str, new_password: str) -> None:
        """Update the credential for an existing provider identity."""
        ...

    def ban_user(self, *, subject: str) -> None:
        """Prevent provider login for this identity."""
        ...

    def unban_user(self, *, subject: str) -> None:
        """Restore provider login for this identity."""
        ...

    def revoke_session(self, *, session_id: str, subject: str) -> None:
        """Revoke all active provider sessions for this identity."""
        ...

    def revoke_subject_sessions(self, *, subject: str) -> None:
        """Revoke every provider session belong to this identity."""
        ...

    def list_successful_login_audit_evidence(
        self, *, timestamp_to: str
    ) -> list[ProviderLoginAuditEvidence]:
        """Read a bounded recent snapshot of supported provider login evidence."""
        ...

    def delete_user(self, *, subject: str) -> None:
        """Remove a never-established identity as compensation.

        Only valid for identities that never completed provisioning.
        Established identities are banned, never deleted.
        """
        ...

    def has_active_session(self, *, session_id: str, subject: str) -> bool:
        """Return whether a provider session belongs to the verified identity."""
        ...
