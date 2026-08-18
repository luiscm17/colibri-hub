"""Pydantic request/response models for Access Control HTTP endpoints.

All models use strict mode and forbid extra fields.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, field_validator

T = TypeVar("T")


class _StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class _AdministrativeMutationRequest(_StrictModel):
    reason: str | None = None

    @field_validator("reason")
    @classmethod
    def _normalized_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


class PaginatedResponse(BaseModel, Generic[T]):
    """Page-based pagination envelope."""

    items: list[T]
    page: int
    page_size: int
    total: int

    model_config = ConfigDict(strict=True)


# --- Requests ---


class CreateRoleRequest(_AdministrativeMutationRequest):
    role_code: str
    role_name: str
    description: str | None = None
    permissions: list["PermissionInput"]


class PermissionInput(_StrictModel):
    action: str
    scope_id: str


class UpdateRoleRequest(_AdministrativeMutationRequest):
    role_name: str
    description: str | None = None
    permissions: list[PermissionInput]
    expected_version: int


class StatusChangeRequest(_AdministrativeMutationRequest):
    is_active: bool
    expected_version: int


class ReplaceUserRolesRequest(_AdministrativeMutationRequest):
    role_ids: list[str]
    expected_version: int


class PreviewRoleChangeRequest(_StrictModel):
    permissions: list[PermissionInput]


class PreviewUserRoleReplacementRequest(_StrictModel):
    role_ids: list[str]


class RegisterScopeRequest(_AdministrativeMutationRequest):
    definition_key: str


class CreateRolePresetRequest(_AdministrativeMutationRequest):
    preset_code: str
    preset_name: str
    description: str | None = None
    permissions: list[PermissionInput]


class UpdateRolePresetRequest(_AdministrativeMutationRequest):
    preset_name: str
    description: str | None = None
    permissions: list[PermissionInput]
    expected_version: int


class CreateRoleFromPresetRequest(_AdministrativeMutationRequest):
    role_code: str
    role_name: str
    description: str | None = None


# --- Responses ---


class PermissionResponse(_StrictModel):
    action: str
    scope_code: str


class PreviewUserResponse(_StrictModel):
    user_id: str
    user_code: str
    display_name: str


class PreviewRoleResponse(_StrictModel):
    role_id: str
    role_code: str
    role_name: str


class ImpactPreviewResponse(_StrictModel):
    subject_version: int
    affected_user_count: int
    affected_users: list[PreviewUserResponse]
    permissions_added: list[PermissionResponse]
    permissions_removed: list[PermissionResponse]
    roles_added: list[PreviewRoleResponse]
    roles_removed: list[PreviewRoleResponse]


class RoleResponse(_StrictModel):
    role_id: str
    role_code: str
    role_name: str
    description: str | None
    is_system_administrator: bool
    is_active: bool
    version: int
    permissions: list[PermissionResponse]


class RolePresetResponse(_StrictModel):
    preset_id: str
    preset_code: str
    preset_name: str
    description: str | None
    is_active: bool
    version: int
    permissions: list[PermissionResponse]


class AccessUserResponse(_StrictModel):
    user_id: str
    identity_subject: str
    user_code: str
    display_name: str
    is_active: bool
    authorization_version: int
    version: int


class AccessUserDetailResponse(_StrictModel):
    """Full user detail with roles, assignments, and permissions."""

    user_id: str
    identity_subject: str
    user_code: str
    display_name: str
    is_active: bool
    authorization_version: int
    version: int
    roles: list["RoleSummaryResponse"]
    assignments: list["AssignmentResponse"]
    is_global: bool
    permissions: list[PermissionResponse]


class AssignmentResponse(_StrictModel):
    assignment_id: str
    role_id: str
    role_code: str
    role_name: str
    assigned_at: str


class ScopeResponse(_StrictModel):
    scope_id: str
    definition_key: str
    scope_code: str
    scope_name: str
    owning_context: str
    is_active: bool
    version: int


class ScopeDefinitionResponse(_StrictModel):
    definition_key: str
    scope_code: str
    scope_name: str
    owning_context: str
    description: str
    supported_actions: list[str]
    is_registered: bool


class AuditEntryResponse(_StrictModel):
    audit_id: str
    operation_id: str
    change_kind: str
    subject_type: str
    subject_id: str
    performed_by_user_id: str | None
    reason: str | None
    occurred_at: str


class AuthorizationResponse(_StrictModel):
    """Authorization section of /access/me response.

    Field `is_global` serializes as `global` per spec §10.1.
    """

    is_global: bool = False
    actions: list[str] = []
    permissions: list[PermissionResponse] = []
    version: int

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        populate_by_name=True,
    )


class RoleSummaryResponse(_StrictModel):
    """Compact role info in /access/me response (spec §10.1)."""

    role_id: str
    code: str
    name: str


class CurrentAccessResponse(_StrictModel):
    user_id: str
    user_code: str
    display_name: str
    is_active: bool
    roles: list[RoleSummaryResponse]
    authorization: AuthorizationResponse
