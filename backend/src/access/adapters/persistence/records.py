from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, JSON, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.record_registry import RecordRegistry


class AccessBootstrapLockRecord(RecordRegistry):
    __tablename__ = "access_bootstrap_lock"
    id: Mapped[int] = mapped_column(primary_key=True)


class AccessProfileRecord(RecordRegistry):
    __tablename__ = "access_profiles"
    __table_args__ = (UniqueConstraint("subject", name="uq_access_profiles_subject"), UniqueConstraint("code", name="uq_access_profiles_code"), Index("ix_access_profiles_active_subject", "subject", postgresql_where=text("is_active")))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AccessRoleRecord(RecordRegistry):
    __tablename__ = "access_roles"
    __table_args__ = (UniqueConstraint("code", name="uq_access_roles_code"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AccessScopeRecord(RecordRegistry):
    __tablename__ = "access_scopes"
    __table_args__ = (UniqueConstraint("code", name="uq_access_scopes_code"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(160), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AccessRolePermissionRecord(RecordRegistry):
    __tablename__ = "access_role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "action", "scope_id", name="uq_access_role_permissions_role_action_scope"), CheckConstraint("action IN ('read', 'write')", name="ck_access_role_permissions_action"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("access_roles.id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    scope_id: Mapped[UUID] = mapped_column(ForeignKey("access_scopes.id", ondelete="RESTRICT"), nullable=False)


class AccessRoleAssignmentRecord(RecordRegistry):
    __tablename__ = "access_role_assignments"
    __table_args__ = (Index("ix_access_role_assignments_current", "profile_id", "role_id", postgresql_where=text("is_current")),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(ForeignKey("access_profiles.id", ondelete="RESTRICT"), nullable=False)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("access_roles.id", ondelete="RESTRICT"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AccessChangeAuditRecord(RecordRegistry):
    __tablename__ = "access_change_audit"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_profile_id: Mapped[UUID | None] = mapped_column(ForeignKey("access_profiles.id", ondelete="RESTRICT"))
    affected_profile_id: Mapped[UUID] = mapped_column(ForeignKey("access_profiles.id", ondelete="RESTRICT"), nullable=False)
    change_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500))
    operation_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    before: Mapped[dict] = mapped_column(JSON, nullable=False)
    after: Mapped[dict] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
