"""Use case: query paginated authentication audit evidence."""

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from auth.domain.errors import ProviderUnavailable
from auth.ports.account_repository import AuthAccountRepository
from auth.ports.audit_repository import AuthAuditEntry, AuthAuditRepository
from auth.ports.identity_provider import IdentityProviderPort


@dataclass(frozen=True, slots=True)
class AuditPage:
    entries: list[AuthAuditEntry]
    cursor: str | None


class InvalidAuditCursor(ValueError):
    """Raised only when a client-supplied audit cursor cannot be decoded."""


class ListAudits:
    """Merge application audits with the current provider login snapshot."""

    def __init__(self, audit_repository: AuthAuditRepository, account_repository: AuthAccountRepository, identity_provider: IdentityProviderPort, clock) -> None:
        self._audits, self._accounts, self._provider, self._clock = audit_repository, account_repository, identity_provider, clock

    def execute(self, *, limit: int = 50, cursor: str | None = None) -> AuditPage:
        key = self._decode(cursor)
        as_of = key[0] if key else self._clock.now().astimezone(timezone.utc).isoformat()
        app_cursor = (key[1], key[3]) if key and key[2] == 0 else None
        application = self._audits.list_keyset(as_of=as_of, cursor=app_cursor, limit=limit + 1)
        provider = self._provider.list_successful_login_audit_evidence(timestamp_to=as_of)
        entries = application + [self._provider_entry(item) for item in provider]
        if key:
            entries = [entry for entry in entries if self._after(entry, key)]
        entries.sort(key=lambda entry: (-datetime.fromisoformat(entry.occurred_at).timestamp(), 0 if entry.source == "application" else 1, entry.audit_id))
        page = entries[:limit]
        return AuditPage(page, self._encode(as_of, page[-1]) if len(entries) > limit else None)

    def _provider_entry(self, item) -> AuthAuditEntry:
        account_id = None
        try:
            if item.subject:
                account = self._accounts.find_by_subject(str(UUID(item.subject)))
                account_id = account.account_id if account else None
        except (ValueError, AttributeError):
            pass
        return AuthAuditEntry(item.entry_id, "", item.event_type, "succeeded", None, account_id, None, None, {}, item.occurred_at, "provider")

    @staticmethod
    def _after(entry: AuthAuditEntry, key: tuple[str, str, int, str]) -> bool:
        occurred_at, entry_id = entry.occurred_at, entry.audit_id
        rank = 0 if entry.source == "application" else 1
        return occurred_at < key[1] or (occurred_at == key[1] and (rank > key[2] or (rank == key[2] and entry_id > key[3])))

    @staticmethod
    def _decode(cursor: str | None) -> tuple[str, str, int, str] | None:
        if not cursor:
            return None
        try:
            raw = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
            if raw["v"] != 1 or raw["source_rank"] not in (0, 1): raise ValueError
            for field in ("as_of", "occurred_at"): datetime.fromisoformat(raw[field])
            return raw["as_of"], raw["occurred_at"], raw["source_rank"], raw["entry_id"]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            raise InvalidAuditCursor("Invalid audit cursor") from None

    @staticmethod
    def _encode(as_of: str, entry: AuthAuditEntry) -> str:
        raw = {"v": 1, "as_of": as_of, "occurred_at": entry.occurred_at, "source_rank": 0 if entry.source == "application" else 1, "entry_id": entry.audit_id}
        return base64.urlsafe_b64encode(json.dumps(raw, separators=(",", ":")).encode()).decode().rstrip("=")
