"""Result dataclasses for access control application use cases."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AccessUserResult:
    user_id: str
    identity_subject: str
    user_code: str
    display_name: str
    is_active: bool
    authorization_version: int
    version: int


@dataclass(frozen=True, slots=True)
class RoleResult:
    role_id: str
    role_code: str
    role_name: str
    description: str | None
    is_system_administrator: bool
    is_active: bool
    version: int
    permissions: list[PermissionResult]


@dataclass(frozen=True, slots=True)
class PermissionResult:
    action: str
    scope_code: str


@dataclass(frozen=True, slots=True)
class ScopeResult:
    scope_id: str
    definition_key: str
    scope_code: str
    scope_name: str
    owning_context: str
    is_active: bool
    version: int


@dataclass(frozen=True, slots=True)
class ScopeDefinitionResult:
    definition_key: str
    scope_code: str
    scope_name: str
    owning_context: str
    description: str
    supported_actions: list[str]
    is_registered: bool


@dataclass(frozen=True, slots=True)
class CurrentAccessResult:
    user_id: str
    user_code: str
    display_name: str
    is_active: bool
    is_global: bool
    permissions: list[PermissionResult]
    authorization_version: int


@dataclass(frozen=True, slots=True)
class AssignmentResult:
    assignment_id: str
    role_id: str
    role_code: str
    role_name: str
    assigned_at: str


@dataclass(frozen=True, slots=True)
class AuditEntryResult:
    audit_id: str
    operation_id: str
    change_kind: str
    subject_type: str
    subject_id: str
    performed_by_user_id: str | None
    reason: str | None
    occurred_at: str
