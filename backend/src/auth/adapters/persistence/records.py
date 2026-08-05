"""SQLAlchemy mapped classes for Authentication tables."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.record_registry import RecordRegistry


class AuthenticationAccountRecord(RecordRegistry):
    """Maps to public.authentication_accounts."""

    __tablename__ = "authentication_accounts"
    __table_args__ = (
        UniqueConstraint(
            "identity_subject",
            name="uq_authentication_accounts_identity_subject",
        ),
        UniqueConstraint(
            "normalized_email",
            name="uq_authentication_accounts_normalized_email",
        ),
        UniqueConstraint(
            "user_code",
            name="uq_authentication_accounts_user_code",
        ),
        CheckConstraint(
            "status IN ('awaiting_password_change', 'active', 'disabled')",
            name="ck_authentication_accounts_status",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_authentication_accounts_version",
        ),
        Index(
            "ix_authentication_accounts_active",
            "identity_subject",
            postgresql_where=text("status <> 'disabled'"),
        ),
        Index(
            "ix_authentication_accounts_email_lookup",
            "normalized_email",
        ),
    )

    authentication_account_id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4
    )
    identity_subject: Mapped[UUID] = mapped_column(nullable=False)
    normalized_email: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    user_code: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'awaiting_password_change'")
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


class AuthenticationAuditRecord(RecordRegistry):
    """Maps to public.authentication_audits. Append-only."""

    __tablename__ = "authentication_audits"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('succeeded', 'failed')",
            name="ck_authentication_audits_outcome",
        ),
        CheckConstraint(
            "event_type IN ("
            "'account_provisioned', 'password_changed', 'password_reset', "
            "'account_disabled', 'account_enabled', 'logout', "
            "'initial_bootstrap', 'login_succeeded', 'login_failed')",
            name="ck_authentication_audits_event_type",
        ),
        Index(
            "ix_authentication_audits_account",
            "affected_account_id",
            "occurred_at",
        ),
        Index("ix_authentication_audits_recent", "occurred_at"),
        Index("ix_authentication_audits_operation", "operation_id"),
    )

    authentication_audit_id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4
    )
    operation_id: Mapped[UUID] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'succeeded'")
    )
    actor_identity_subject: Mapped[UUID | None] = mapped_column(nullable=True)
    affected_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "authentication_accounts.authentication_account_id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    provider_session_id: Mapped[UUID | None] = mapped_column(nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(
        JSON, nullable=False, server_default=text("'{}'::jsonb")
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
