"""SQLAlchemy implementation of the Authentication audit repository port."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.adapters.persistence.records import AuthenticationAuditRecord
from auth.ports.audit_repository import AuthAuditEntry


class AuthAuditRepositoryAdapter:
    """PostgreSQL-backed append-only audit repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, entry: AuthAuditEntry) -> None:
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

    def list_by_account(self, account_id: str) -> list[AuthAuditEntry]:
        stmt = (
            select(AuthenticationAuditRecord)
            .where(
                AuthenticationAuditRecord.affected_account_id == UUID(account_id)
            )
            .order_by(AuthenticationAuditRecord.occurred_at.desc())
        )
        records = self._session.scalars(stmt).all()
        return [self._to_entry(r) for r in records]

    def list_recent(self, limit: int = 50) -> list[AuthAuditEntry]:
        stmt = (
            select(AuthenticationAuditRecord)
            .order_by(AuthenticationAuditRecord.occurred_at.desc())
            .limit(limit)
        )
        records = self._session.scalars(stmt).all()
        return [self._to_entry(r) for r in records]

    def record_login_outcome(
        self,
        *,
        audit_id: str,
        operation_id: str,
        event_type: str,
        outcome: str,
        actor_identity_subject: str | None = None,
        affected_account_id: str | None = None,
        provider_session_id: str | None = None,
        occurred_at: str,
    ) -> None:
        """Persist a login_succeeded or login_failed audit event.

        This is the C5 skeleton write path. The caller hook (provider webhook
        or login adapter) is not wired yet — production wiring deferred.
        """
        entry = AuthAuditEntry(
            audit_id=audit_id,
            operation_id=operation_id,
            event_type=event_type,
            outcome=outcome,
            actor_identity_subject=actor_identity_subject,
            affected_account_id=affected_account_id,
            provider_session_id=provider_session_id,
            reason=None,
            details={},
            occurred_at=occurred_at,
        )
        self.append(entry)

    @staticmethod
    def _to_entry(record: AuthenticationAuditRecord) -> AuthAuditEntry:
        return AuthAuditEntry(
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
