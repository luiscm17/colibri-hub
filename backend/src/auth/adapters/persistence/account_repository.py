"""SQLAlchemy implementation of the Authentication account repository port."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.adapters.persistence.records import AuthenticationAccountRecord
from auth.domain.account import AuthenticationAccount
from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.email import NormalizedEmail


class AuthAccountRepositoryAdapter:
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
