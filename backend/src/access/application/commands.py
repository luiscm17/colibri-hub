"""Command dataclasses for access control application use cases."""

from __future__ import annotations

from dataclasses import dataclass


class _OptionalAdministrativeReason:
    reason: str | None

    def __post_init__(self) -> None:
        if self.reason is None:
            return

        normalized = self.reason.strip()
        object.__setattr__(self, "reason", normalized or None)


@dataclass(frozen=True, slots=True)
class CreateAccessUserCommand:
    """Internal command: create an access profile during unified provisioning."""

    identity_subject: str
    user_code: str
    display_name: str
    role_codes: list[str]
    actor_subject: str
    reason: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class ActivateAccessUserCommand:
    subject: str
    actor_subject: str
    reason: str | None
    operation_id: str


@dataclass(frozen=True, slots=True)
class DeactivateAccessUserCommand:
    subject: str
    actor_subject: str
    reason: str | None
    operation_id: str


@dataclass(frozen=True, slots=True)
class AdministrativeProfileLifecycleCommand(_OptionalAdministrativeReason):
    subject: str
    actor_subject: str
    reason: str | None
    operation_id: str


@dataclass(frozen=True, slots=True)
class CreateRoleCommand(_OptionalAdministrativeReason):
    role_code: str
    role_name: str
    description: str | None
    permissions: list[PermissionInput]
    reason: str | None
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class UpdateRoleCommand(_OptionalAdministrativeReason):
    role_id: str
    role_name: str
    description: str | None
    permissions: list[PermissionInput]
    expected_version: int
    reason: str | None
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class ActivateRoleCommand(_OptionalAdministrativeReason):
    role_id: str
    expected_version: int
    reason: str | None
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class DeactivateRoleCommand(_OptionalAdministrativeReason):
    role_id: str
    expected_version: int
    reason: str | None
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class ReplaceUserRolesCommand(_OptionalAdministrativeReason):
    user_id: str
    role_ids: list[str]
    expected_version: int
    reason: str | None
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class RegisterRecognizedScopeCommand(_OptionalAdministrativeReason):
    definition_key: str
    reason: str | None
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class ActivateScopeCommand(_OptionalAdministrativeReason):
    scope_id: str
    expected_version: int
    reason: str | None
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class DeactivateScopeCommand(_OptionalAdministrativeReason):
    scope_id: str
    expected_version: int
    reason: str | None
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class PermissionInput:
    """A single permission entry in a role configuration request."""

    action: str
    scope_id: str


@dataclass(frozen=True, slots=True)
class CreateRolePresetCommand(_OptionalAdministrativeReason):
    preset_code: str
    preset_name: str
    description: str | None
    permissions: list[PermissionInput]
    reason: str | None
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class UpdateRolePresetCommand(_OptionalAdministrativeReason):
    preset_id: str
    preset_name: str
    description: str | None
    permissions: list[PermissionInput]
    expected_version: int
    reason: str | None
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class ChangeRolePresetStatusCommand(_OptionalAdministrativeReason):
    preset_id: str
    is_active: bool
    expected_version: int
    reason: str | None
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class CreateRoleFromPresetCommand(_OptionalAdministrativeReason):
    preset_id: str
    role_code: str
    role_name: str
    description: str | None
    reason: str | None
    actor_user_id: str
    operation_id: str
