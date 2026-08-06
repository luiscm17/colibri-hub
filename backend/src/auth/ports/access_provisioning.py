"""Port for coordinating with Access Control during provisioning and state changes.

Authentication consumes Access Control policies but does not reproduce role semantics.
"""

from typing import Protocol


class AccessProvisioningPort(Protocol):
    """Create, activate, or deactivate the associated Access profile and assign roles."""

    def provision_profile(
        self,
        *,
        subject: str,
        profile_code: str,
        display_name: str = "",
        role_codes: list[str],
        actor_subject: str,
        reason: str,
        operation_id: str,
    ) -> None:
        """Create an Access profile and assign initial roles for a newly provisioned account.

        Args:
            display_name: The user's display name. Falls back to profile_code if empty.

        Raises if role_codes is empty, contains duplicates, or references inactive roles.
        """
        ...

    def activate_profile(
        self,
        *,
        subject: str,
        actor_subject: str,
        reason: str,
        operation_id: str,
    ) -> None:
        """Reactivate an Access profile (on account re-enablement)."""
        ...

    def deactivate_profile(
        self,
        *,
        subject: str,
        actor_subject: str,
        reason: str,
        operation_id: str,
    ) -> None:
        """Deactivate an Access profile (on account disablement)."""
        ...

    def would_remove_last_administrator(self, subject: str) -> bool:
        """Check if disabling/resetting this subject would remove the last operational admin.

        Returns True if the operation should be rejected.
        """
        ...
