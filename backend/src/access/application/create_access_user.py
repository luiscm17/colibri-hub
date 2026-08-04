"""Use case: create an access user during unified provisioning (internal contract §10.6)."""

from access.application.dto import AccessUserResult, CreateAccessUserCommand
from access.domain.errors import (
    DuplicateAccessIdentity,
    DuplicateUserCode,
    InactiveAccessRole,
    AccessRoleNotFound,
)
from access.ports.repositories import (
    AccessAuditRepository,
    AccessUserRepository,
    RoleRepository,
)
from access.ports.clock import ClockPort
from access.ports.identity import IdentityPort
from access.ports.transaction import TransactionPort


class CreateAccessUser:
    """Create an Access profile with initial role assignments.

    Called internally by Authentication's ProvisionAccount — never exposed as
    a public HTTP endpoint. Shares the caller's transaction boundary.
    """

    def __init__(
        self,
        *,
        user_repository: AccessUserRepository,
        role_repository: RoleRepository,
        audit_repository: AccessAuditRepository,
        transaction: TransactionPort,
        clock: ClockPort,
        identity: IdentityPort,
    ) -> None:
        self._users = user_repository
        self._roles = role_repository
        self._audits = audit_repository
        self._transaction = transaction
        self._clock = clock
        self._identity = identity

    def execute(self, command: CreateAccessUserCommand) -> AccessUserResult:
        if not command.role_codes:
            raise ValueError("At least one role_code is required for provisioning.")

        with self._transaction.atomic():
            # Validate uniqueness
            if self._users.find_by_subject(command.identity_subject) is not None:
                raise DuplicateAccessIdentity()

            # Resolve and validate roles
            roles = []
            for code in command.role_codes:
                role = self._roles.find_by_code(code)
                if role is None:
                    raise AccessRoleNotFound()
                if not role.is_active:
                    raise InactiveAccessRole()
                roles.append(role)

            # Check duplicates in requested roles
            if len(set(command.role_codes)) != len(command.role_codes):
                raise ValueError("Duplicate role codes in provisioning request.")

            now = self._clock.now()
            from access.domain.users import AccessUser
            from access.domain.roles import Assignment

            user = AccessUser(
                user_id=self._identity.generate_id(),
                identity_subject=command.identity_subject,
                user_code=command.user_code,
                display_name=command.display_name,
                is_active=True,
                authorization_version=1,
                version=1,
                created_at=now,
                updated_at=now,
            )
            self._users.save(user)

            # Assign roles
            actor_user_id = self._resolve_actor(command.actor_subject)
            for role in roles:
                assignment = Assignment(
                    assignment_id=self._identity.generate_id(),
                    user_id=user.user_id,
                    role_id=role.role_id,
                    assigned_by_user_id=actor_user_id,
                    assigned_at=now,
                )
                self._roles.save_assignment(assignment)

            # Audit
            self._audits.append(
                operation_id=command.operation_id,
                change_kind="user_provisioned",
                subject_type="user",
                subject_id=user.user_id,
                performed_by_user_id=actor_user_id,
                reason=command.reason,
                before_values={},
                after_values={
                    "user_code": user.user_code,
                    "display_name": user.display_name,
                    "role_codes": command.role_codes,
                },
            )

        return AccessUserResult(
            user_id=user.user_id,
            identity_subject=user.identity_subject,
            user_code=user.user_code,
            display_name=user.display_name,
            is_active=user.is_active,
            authorization_version=user.authorization_version,
            version=user.version,
        )

    def _resolve_actor(self, actor_subject: str) -> str:
        """Resolve the acting user's internal ID from their identity subject."""
        actor = self._users.find_by_subject(actor_subject)
        if actor is None:
            raise ValueError(f"Actor subject '{actor_subject}' not found in access users.")
        return actor.user_id
