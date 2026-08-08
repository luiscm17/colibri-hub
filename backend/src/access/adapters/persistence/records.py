"""SQLAlchemy mapped classes for Access Control tables."""

from datetime import datetime
from uuid import UUID, uuid4

from infra.persistence.record_registry import RecordRegistry
from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class AccessScopeDefinitionRecord(RecordRegistry):
    """Maps to public.access_scope_definitions (immutable catalog)."""

    __tablename__ = "access_scope_definitions"
    __table_args__ = (
        UniqueConstraint("scope_code", name="uq_access_scope_definitions_code"),
    )

    definition_key: Mapped[str] = mapped_column(
        String(160), primary_key=True
    )
    scope_code: Mapped[str] = mapped_column(String(160), nullable=False)
    scope_name: Mapped[str] = mapped_column(String(200), nullable=False)
    owning_context: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    supported_actions: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False
    )


class AccessUserRecord(RecordRegistry):
    """Maps to public.access_users."""

    __tablename__ = "access_users"
    __table_args__ = (
        UniqueConstraint(
            "identity_subject", name="uq_access_users_identity_subject"
        ),
        UniqueConstraint("user_code", name="uq_access_users_user_code"),
    )

    user_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    identity_subject: Mapped[str] = mapped_column(Text, nullable=False)
    user_code: Mapped[str] = mapped_column(String(40), nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    authorization_version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class AccessRoleRecord(RecordRegistry):
    """Maps to public.access_roles."""

    __tablename__ = "access_roles"
    __table_args__ = (
        UniqueConstraint("role_code", name="uq_access_roles_role_code"),
        Index(
            "uq_access_roles_single_sysadmin",
            "is_system_administrator",
            unique=True,
            postgresql_where=text("is_system_administrator"),
        ),
    )

    role_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    role_code: Mapped[str] = mapped_column(String(80), nullable=False)
    role_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system_administrator: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class AccessScopeRecord(RecordRegistry):
    """Maps to public.access_scopes."""

    __tablename__ = "access_scopes"
    __table_args__ = (
        UniqueConstraint(
            "definition_key", name="uq_access_scopes_definition_key"
        ),
        UniqueConstraint("scope_code", name="uq_access_scopes_scope_code"),
    )

    scope_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    definition_key: Mapped[str] = mapped_column(
        String(160),
        ForeignKey(
            "access_scope_definitions.definition_key", ondelete="RESTRICT"
        ),
        nullable=False,
    )
    scope_code: Mapped[str] = mapped_column(String(160), nullable=False)
    scope_name: Mapped[str] = mapped_column(String(200), nullable=False)
    owning_context: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class AccessRolePermissionRecord(RecordRegistry):
    """Maps to public.access_role_permissions."""

    __tablename__ = "access_role_permissions"
    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "scope_id",
            "action",
            name="uq_access_role_permissions_triple",
        ),
        CheckConstraint(
            "action IN ('read', 'write', 'edit', 'edit_outside_window', 'manage_access')",
            name="ck_access_role_permissions_action",
        ),
    )

    role_permission_id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("access_roles.role_id", ondelete="RESTRICT"), nullable=False
    )
    scope_id: Mapped[UUID] = mapped_column(
        ForeignKey("access_scopes.scope_id", ondelete="RESTRICT"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("access_users.user_id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class AccessRolePresetRecord(RecordRegistry):
    __tablename__ = "access_role_presets"
    __table_args__ = (UniqueConstraint("preset_code", name="uq_access_role_presets_preset_code"),)
    preset_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    preset_code: Mapped[str] = mapped_column(String(80), nullable=False)
    preset_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class AccessRolePresetPermissionRecord(RecordRegistry):
    __tablename__ = "access_role_preset_permissions"
    __table_args__ = (
        UniqueConstraint("preset_id", "scope_id", "action", name="uq_access_role_preset_permissions_triple"),
        CheckConstraint("action IN ('read', 'write', 'edit', 'edit_outside_window', 'manage_access')", name="ck_access_role_preset_permissions_action"),
    )
    preset_permission_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    preset_id: Mapped[UUID] = mapped_column(ForeignKey("access_role_presets.preset_id", ondelete="RESTRICT"), nullable=False)
    scope_id: Mapped[UUID] = mapped_column(ForeignKey("access_scopes.scope_id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("access_users.user_id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class AccessUserRoleAssignmentRecord(RecordRegistry):
    """Maps to public.access_user_role_assignments."""

    __tablename__ = "access_user_role_assignments"
    __table_args__ = (
        Index(
            "uq_access_assignments_current",
            "user_id",
            "role_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
        CheckConstraint(
            "(revoked_at IS NULL AND revoked_by_user_id IS NULL AND revoke_reason IS NULL) OR "
            "(revoked_at IS NOT NULL AND revoked_by_user_id IS NOT NULL AND revoke_reason IS NOT NULL)",
            name="ck_access_assignments_revocation",
        ),
    )

    assignment_id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("access_users.user_id", ondelete="RESTRICT"), nullable=False
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("access_roles.role_id", ondelete="RESTRICT"), nullable=False
    )
    assigned_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("access_users.user_id", ondelete="RESTRICT"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    revoked_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("access_users.user_id", ondelete="RESTRICT"), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoke_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class AccessChangeAuditRecord(RecordRegistry):
    """Maps to public.access_change_audits. Append-only."""

    __tablename__ = "access_change_audits"
    __table_args__ = (
        CheckConstraint(
            "(change_kind = 'initial_bootstrap' AND performed_by_user_id IS NULL) OR "
            "(change_kind <> 'initial_bootstrap' AND performed_by_user_id IS NOT NULL)",
            name="ck_access_change_audits_actor",
        ),
        Index(
            "ix_access_change_audits_subject",
            "subject_type",
            "subject_id",
        ),
        Index("ix_access_change_audits_recent", "occurred_at"),
    )

    access_change_audit_id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4
    )
    operation_id: Mapped[UUID] = mapped_column(nullable=False)
    change_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(40), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(nullable=False)
    performed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("access_users.user_id", ondelete="RESTRICT"), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_values: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    after_values: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
