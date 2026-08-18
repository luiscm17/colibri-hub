"""Use case: replace the complete role set for an access user."""

from access.application.commands import ReplaceUserRolesCommand
from access.domain.errors import (
    AccessRoleNotFound,
    AccessUserNotFound,
    AccessVersionConflict,
    InactiveAccessRole,
    LastSystemAdministratorRequired,
)
from access.ports.clock import ClockPort
from access.ports.identity import IdentityPort
from access.ports.assignments import AssignmentRepository
from access.ports.audit import AccessAuditRepository
from access.ports.roles import RoleRepository
from access.ports.users import AccessUserRepository
from access.ports.transaction import TransactionPort


class ReplaceUserRoles:
    """Atomically replace all current role assignments for a user.

    Closes removed assignments, creates new ones, preserves unchanged,
    bumps authorization_version, and writes one audit entry.
    """

    def __init__(
        self,
        *,
        user_repository: AccessUserRepository,
        role_repository: RoleRepository,
        assignment_repository: AssignmentRepository,
        audit_repository: AccessAuditRepository,
        transaction: TransactionPort,
        clock: ClockPort,
        identity: IdentityPort,
    ) -> None:
        self._users = user_repository
        self._roles = role_repository
        self._assignments = assignment_repository
        self._audits = audit_repository
        self._transaction = transaction
        self._clock = clock
        self._identity = identity

    def execute(self, command: ReplaceUserRolesCommand) -> None:
        with self._transaction.atomic():
            user = self._users.find_by_id(command.user_id)
            if user is None:
                raise AccessUserNotFound()
            if user.version != command.expected_version:
                raise AccessVersionConflict()

            # Validate requested roles exist and are active
            new_roles = []
            for role_id in command.role_ids:
                role = self._roles.find_by_id(role_id)
                if role is None:
                    raise AccessRoleNotFound()
                if not role.is_active:
                    raise InactiveAccessRole()
                new_roles.append(role)

            # Current assignments
            current_assignments = self._assignments.find_for_user(user.user_id)
            current_role_ids = {a.role_id for a in current_assignments if a.is_current}
            desired_role_ids = set(command.role_ids)

            # Last-admin check: if removing sysadmin role from this user
            sysadmin_role = self._roles.find_system_administrator_role()
            if (
                sysadmin_role
                and sysadmin_role.role_id in current_role_ids
                and sysadmin_role.role_id not in desired_role_ids
            ):
                remaining = self._users.count_active_administrators(
                    exclude_user_id=user.user_id, for_update=True
                )
                if remaining < 1:
                    raise LastSystemAdministratorRequired()

            now = self._clock.now()

            # Snapshot audit values before mutation
            previous_codes = sorted(
                r.role_code
                for a in current_assignments
                if a.is_current
                for r in [self._roles.find_by_id(a.role_id)]
                if r
            )
            resulting_codes = sorted(r.role_code for r in new_roles)

            # Revoke removed assignments
            for assignment in current_assignments:
                if assignment.is_current and assignment.role_id not in desired_role_ids:
                    assignment.revoke(
                        by=command.actor_user_id,
                        reason=command.reason,
                        at=now,
                    )
                    self._assignments.save(assignment)

            # Create new assignments
            from access.domain.roles import Assignment

            for role_id in desired_role_ids - current_role_ids:
                assignment = Assignment(
                    assignment_id=self._identity.generate_id(),
                    user_id=user.user_id,
                    role_id=role_id,
                    assigned_by_user_id=command.actor_user_id,
                    assigned_at=now,
                )
                self._assignments.save(assignment)

            # Bump authorization version
            user.authorization_version += 1
            user.version += 1
            user.updated_at = now
            self._users.save(user)

            self._audits.append(
                operation_id=command.operation_id,
                change_kind="user_roles_replaced",
                subject_type="user",
                subject_id=user.user_id,
                performed_by_user_id=command.actor_user_id,
                reason=command.reason,
                before_values={"role_codes": previous_codes},
                after_values={"role_codes": resulting_codes},
            )
