"""Pydantic request/response models for Access Control HTTP endpoints.

All models use strict mode and forbid extra fields.
"""

from pydantic import BaseModel, ConfigDict


class _StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


# --- Requests ---


class CreateRoleRequest(_StrictModel):
    role_code: str
    role_name: str
    description: str | None = None
    permissions: list["PermissionInput"]
    reason: str


class PermissionInput(_StrictModel):
    action: str
    scope_id: str


class UpdateRoleRequest(_StrictModel):
    role_name: str
    description: str | None = None
    permissions: list[PermissionInput]
    expected_version: int
    reason: str


class StatusChangeRequest(_StrictModel):
    is_active: bool
    expected_version: int
    reason: str


class ReplaceUserRolesRequest(_StrictModel):
    role_ids: list[str]
    expected_version: int
    reason: str


class RegisterScopeRequest(_StrictModel):
    definition_key: str
    reason: str


# --- Responses ---


class PermissionResponse(_StrictModel):
    action: str
    scope_code: str


class RoleResponse(_StrictModel):
    role_id: str
    role_code: str
    role_name: str
    description: str | None
    is_system_administrator: bool
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
    """Authorization section of /access/me response."""

    global_access: bool = False
    actions: list[str] = []
    permissions: list[PermissionResponse] = []
    version: int

    model_config = ConfigDict(strict=True, extra="forbid", populate_by_name=True)


class CurrentAccessResponse(_StrictModel):
    user_id: str
    user_code: str
    display_name: str
    is_active: bool
    authorization: AuthorizationResponse
