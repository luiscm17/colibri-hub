"""Command dataclasses for access control application use cases."""

from __future__ import annotations

from dataclasses import dataclass


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
    reason: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class DeactivateAccessUserCommand:
    subject: str
    actor_subject: str
    reason: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class CreateRoleCommand:
    role_code: str
    role_name: str
    description: str | None
    permissions: list[PermissionInput]
    reason: str
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class UpdateRoleCommand:
    role_id: str
    role_name: str
    description: str | None
    permissions: list[PermissionInput]
    expected_version: int
    reason: str
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class ActivateRoleCommand:
    role_id: str
    expected_version: int
    reason: str
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class DeactivateRoleCommand:
    role_id: str
    expected_version: int
    reason: str
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class ReplaceUserRolesCommand:
    user_id: str
    role_ids: list[str]
    expected_version: int
    reason: str
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class RegisterRecognizedScopeCommand:
    definition_key: str
    reason: str
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class ActivateScopeCommand:
    scope_id: str
    expected_version: int
    reason: str
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class DeactivateScopeCommand:
    scope_id: str
    expected_version: int
    reason: str
    actor_user_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class PermissionInput:
    """A single permission entry in a role configuration request."""

    action: str
    scope_id: str
