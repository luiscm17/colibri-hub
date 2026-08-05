"""Use case: record and terminate a logout."""

from auth.domain.errors import AccountNotFound
from auth.ports.account_repository import AuthAccountRepository
from auth.ports.audit_repository import AuthAuditEntry, AuthAuditRepository
from auth.ports.clock import ClockPort
from auth.ports.identity import IdentityPort
from auth.ports.identity_provider import IdentityProviderPort


class RecordLogout:
    """Request revocation of the current provider session and record the event.

    Idempotent when the provider session has already ended.
    """

    def __init__(
        self,
        *,
        account_repository: AuthAccountRepository,
        audit_repository: AuthAuditRepository,
        identity_provider: IdentityProviderPort,
        clock: ClockPort,
        identity: IdentityPort,
    ) -> None:
        self._accounts = account_repository
        self._audits = audit_repository
        self._provider = identity_provider
        self._clock = clock
        self._identity = identity

    def execute(self, *, identity_subject: str, session_id: str | None) -> None:
        account = self._accounts.find_by_subject(identity_subject)
        if account is None:
            raise AccountNotFound(identity_subject)

        # Revoke provider session (idempotent if already ended)
        self._provider.revoke_sessions(subject=identity_subject)

        now = self._clock.now()
        self._audits.append(
            AuthAuditEntry(
                audit_id=self._identity.generate_id(),
                operation_id=self._identity.generate_operation_id(),
                event_type="logout",
                outcome="succeeded",
                actor_identity_subject=identity_subject,
                affected_account_id=account.account_id,
                provider_session_id=session_id,
                reason=None,
                details={},
                occurred_at=now.isoformat(),
            )
        )
