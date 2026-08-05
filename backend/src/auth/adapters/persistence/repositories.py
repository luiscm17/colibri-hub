"""SQLAlchemy implementations of Authentication repository ports."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.adapters.persistence.models import (
    AuthenticationAccountRecord,
    AuthenticationAuditRecord,
)
from auth.domain.account import AuthenticationAccount
from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.email import NormalizedEmail
from auth.ports.audit_repository import AuditEntry


class AccountRepositoryAdapter:
    """PostgreSQL-backed account repository with optimistic concurrency."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_subject(self, identity_subject: str) -> AuthenticationAccount | None:
        stmt = select(AuthenticationAccountRecord).where(
            AuthenticationAccountRecord.identity_subject == UUID(identity_subject)
        )
        record = self._session.scalars(stmt).first()
        return self._to_domain(record) if record else None

    def find_by_email(self, email: NormalizedEmail) -> AuthenticationAccount | None:
        stmt = select(AuthenticationAccountRecord).where(
            AuthenticationAccountRecord.normalized_email == email.value
        )
        record = self._session.scalars(stmt).first()
        return self._to_domain(record) if record else None

    def find_by_id(self, account_id: str) -> AuthenticationAccount | None:
        stmt = select(AuthenticationAccountRecord).where(
            AuthenticationAccountRecord.authentication_account_id == UUID(account_id)
        )
        record = self._session.scalars(stmt).first()
        return self._to_domain(record) if record else None

    def list_all(self) -> list[AuthenticationAccount]:
        stmt = select(AuthenticationAccountRecord).order_by(
            AuthenticationAccountRecord.created_at
        )
        records = self._session.scalars(stmt).all()
        return [self._to_domain(r) for r in records]

    def list_enabled_administrators(self) -> list[AuthenticationAccount]:
        stmt = select(AuthenticationAccountRecord).where(
            AuthenticationAccountRecord.status != "disabled"
        )
        records = self._session.scalars(stmt).all()
        return [self._to_domain(r) for r in records]

    def save(self, account: AuthenticationAccount) -> None:
        existing = self._session.get(
            AuthenticationAccountRecord,
            UUID(account.account_id),
        )
        if existing is None:
            record = AuthenticationAccountRecord(
                authentication_account_id=UUID(account.account_id),
                identity_subject=UUID(account.identity_subject),
                normalized_email=account.normalized_email.value,
                display_name=account.display_name,
                user_code=account.user_code,
                status=account.status.value,
                version=account.version,
            )
            if account.created_at is not None:
                record.created_at = account.created_at
            if account.updated_at is not None:
                record.updated_at = account.updated_at
            self._session.add(record)
        else:
            existing.status = account.status.value
            existing.display_name = account.display_name
            existing.version = account.version
            if account.updated_at is not None:
                existing.updated_at = account.updated_at
        self._session.flush()

    @staticmethod
    def _to_domain(record: AuthenticationAccountRecord) -> AuthenticationAccount:
        return AuthenticationAccount(
            account_id=str(record.authentication_account_id),
            identity_subject=str(record.identity_subject),
            normalized_email=NormalizedEmail(value=record.normalized_email),
            status=AuthenticationAccountStatus(record.status),
            display_name=record.display_name,
            user_code=record.user_code,
            version=record.version,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


class AuditRepositoryAdapter:
    """PostgreSQL-backed append-only audit repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, entry: AuditEntry) -> None:
        record = AuthenticationAuditRecord(
            authentication_audit_id=UUID(entry.audit_id),
            operation_id=UUID(entry.operation_id),
            event_type=entry.event_type,
            outcome=entry.outcome,
            actor_identity_subject=(
                UUID(entry.actor_identity_subject)
                if entry.actor_identity_subject
                else None
            ),
            affected_account_id=(
                UUID(entry.affected_account_id)
                if entry.affected_account_id
                else None
            ),
            provider_session_id=(
                UUID(entry.provider_session_id)
                if entry.provider_session_id
                else None
            ),
            reason=entry.reason,
            details=entry.details,
            occurred_at=(
                datetime.fromisoformat(entry.occurred_at)
                if entry.occurred_at
                else None
            ),
        )
        self._session.add(record)
        self._session.flush()

    def list_by_account(self, account_id: str) -> list[AuditEntry]:
        stmt = (
            select(AuthenticationAuditRecord)
            .where(
                AuthenticationAuditRecord.affected_account_id == UUID(account_id)
            )
            .order_by(AuthenticationAuditRecord.occurred_at.desc())
        )
        records = self._session.scalars(stmt).all()
        return [self._to_entry(r) for r in records]

    def list_recent(self, limit: int = 50) -> list[AuditEntry]:
        stmt = (
            select(AuthenticationAuditRecord)
            .order_by(AuthenticationAuditRecord.occurred_at.desc())
            .limit(limit)
        )
        records = self._session.scalars(stmt).all()
        return [self._to_entry(r) for r in records]

    @staticmethod
    def _to_entry(record: AuthenticationAuditRecord) -> AuditEntry:
        return AuditEntry(
            audit_id=str(record.authentication_audit_id),
            operation_id=str(record.operation_id),
            event_type=record.event_type,
            outcome=record.outcome,
            actor_identity_subject=(
                str(record.actor_identity_subject)
                if record.actor_identity_subject
                else None
            ),
            affected_account_id=(
                str(record.affected_account_id)
                if record.affected_account_id
                else None
            ),
            provider_session_id=(
                str(record.provider_session_id)
                if record.provider_session_id
                else None
            ),
            reason=record.reason,
            details=record.details or {},
            occurred_at=(
                record.occurred_at.isoformat() if record.occurred_at else None
            ),
        )
