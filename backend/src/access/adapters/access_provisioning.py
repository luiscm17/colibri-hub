"""Adapter implementing auth.ports.access_provisioning.AccessProvisioningPort.

Delegates to Access application use cases, sharing the Auth session
for transactional coordination during unified provisioning.
"""

from access.adapters.persistence.user_repository import (
    AccessUserRepositoryAdapter,
)
from access.application.activate_access_user import ActivateAccessUser
from access.application.create_access_user import CreateAccessUser
from access.application.deactivate_access_user import DeactivateAccessUser
from access.application.commands import (
    ActivateAccessUserCommand,
    CreateAccessUserCommand,
    DeactivateAccessUserCommand,
)


class AccessProvisioningAdapter:
    """Implements AccessProvisioningPort by delegating to Access use cases.

    Built inside auth_use_case_factory(session) so it shares the same
    SQLAlchemy session as Auth — making provisioning atomic.
    """

    def __init__(
        self,
        *,
        create_user: CreateAccessUser,
        activate_user: ActivateAccessUser,
        deactivate_user: DeactivateAccessUser,
        user_repository: AccessUserRepositoryAdapter,
    ) -> None:
        self._create = create_user
        self._activate = activate_user
        self._deactivate = deactivate_user
        self._users = user_repository

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
        self._create.execute(CreateAccessUserCommand(
            identity_subject=subject,
            user_code=profile_code,
            display_name=display_name or profile_code,
            role_codes=role_codes,
            actor_subject=actor_subject,
            reason=reason,
            operation_id=operation_id,
        ))

    def activate_profile(
        self,
        *,
        subject: str,
        actor_subject: str,
        reason: str,
        operation_id: str,
    ) -> None:
        self._activate.execute(ActivateAccessUserCommand(
            subject=subject,
            actor_subject=actor_subject,
            reason=reason,
            operation_id=operation_id,
        ))

    def deactivate_profile(
        self,
        *,
        subject: str,
        actor_subject: str,
        reason: str,
        operation_id: str,
    ) -> None:
        self._deactivate.execute(DeactivateAccessUserCommand(
            subject=subject,
            actor_subject=actor_subject,
            reason=reason,
            operation_id=operation_id,
        ))

    def would_remove_last_administrator(self, subject: str) -> bool:
        user = self._users.find_by_subject(subject)
        if user is None:
            return False
        count = self._users.count_active_administrators(
            exclude_user_id=user.user_id, for_update=True
        )
        return count < 1
