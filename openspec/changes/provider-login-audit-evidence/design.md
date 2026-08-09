# Design: Provider Login Audit Evidence

## Technical Approach

**Ready for revised PR3 tasks.** `ListAudits` merges unchanged application audits with a bounded recent snapshot of available successful-login evidence from server-only `GET /auth/v1/admin/audit`. This is not a forensic archive: it claims no provider history, retention duration, provider keyset/candidate completeness, attested equal-time ties, or cross-request continuity. Failed login/BR33 remain partial.

## Architecture Decisions

| Decision | Options and trade-off | Choice and rationale |
|---|---|---|
| Provider boundary | New port; extend existing port. | Extend `IdentityProviderPort`; provider ownership already sits with sessions. |
| Provider access | Direct Auth PostgreSQL, grants/RPC, or Admin API. | Server-only Admin API only; no new persistence/security surface. |
| Resource admission | Decode then count; transport-bound streaming. | Bound bytes before JSON decode, then bound entries; neither untrusted body nor candidate list is unbounded. |
| Duplicate IDs | Deduplicate; reject. | Reject duplicate non-empty IDs atomically: it preserves at-most-once evidence without choosing a lossy winner. |
| Pagination | Claim frozen provider history; order each read honestly. | Preserve PR2 opaque keyset; deterministically order the current visible snapshot with the application page only. |

## Data Flow

```text
Administrator -> ListAudits -> application keyset (UTC as_of)
                           -> streamed Admin Audit body -> bounded array/map
                           -> UUID correlation -> ordered current-snapshot page
```

## Bounded Snapshot Ingestion

Set `MAX_PROVIDER_AUDIT_ENTRIES = 500`, `MAX_PROVIDER_AUDIT_ENTRY_BYTES = 4096`, and `MAX_PROVIDER_AUDIT_RESPONSE_BYTES = 2 + MAX_PROVIDER_AUDIT_ENTRIES * (MAX_PROVIDER_AUDIT_ENTRY_BYTES + 1)` (2,048,502 bytes). This proportional ceiling includes `[]` and one comma per possible entry; it is the smallest adapter-local bound that limits the full untrusted response without infrastructure.

The installed GoTrue `_request` uses `httpx.Client.request`, which eagerly reads the response; it cannot enforce this bound before decoding. The adapter therefore uses the available **private** GoTrue seam `auth._http_client.stream(...)`, with `auth._url`, `auth._headers`, and `QueryParams({"timestamp_to": as_of})`, to call the same Admin Audit endpoint. It rejects a numeric `Content-Length` above the ceiling before reading; otherwise it accumulates `iter_bytes()` only up to the ceiling plus one byte, then decodes UTF-8 JSON once. HTTP status, stream, truncation, invalid UTF-8/JSON, and oversized bodies become `ProviderUnavailable`. This private-seam version risk is explicit; PR3 pins the existing client behavior with adapter tests and must revisit it on Supabase Auth upgrades.

Accept only a top-level array. Reject atomically when it has 501 entries; an item is not an object; a non-empty string `id` repeats; `created_at` is not timezone-aware or is after the cutoff; or `payload` is not an object with string `action`. Filter/map only `action == "login"`; UUID `actor_id` is optional, otherwise `subject=None`. Expose only `entry_id`, `occurred_at`, optional `subject`, and `login_succeeded`. Transport, authorization, malformed/required-field, duplicate-ID, and size failures remain atomic `503 authentication_provider_unavailable`.

## Pagination

PR2 already rereads provider evidence per request and applies `{v, as_of, occurred_at, source_rank, entry_id}` after merging. `(occurred_at DESC, application-before-provider, entry_id ASC)` is deterministic for the current visible snapshot and application page. No cursor schema or `ListAudits` algorithm change is required; replace only adapter envelope/completeness/retention validation and wording that calls provider evidence “complete.” Retain `as_of` for application keysets and provider timestamp validation.

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/src/auth/adapters/identity_provider/admin_client.py` | Modify | Private HTTPX-streamed body ceiling; array, count, safe-field, and duplicate-ID admission. |
| `backend/src/auth/ports/identity_provider.py` | Modify | Describe a bounded recent snapshot, not a complete set. |
| `backend/src/auth/application/list_audits.py` | Modify | Correct completeness wording only; preserve PR2 cursor/merge. |
| `backend/tests/test_auth_adapter_provider.py` | Modify | Streaming-boundary, malformed, duplicate-ID, and 500/501 RED/GREEN tests. |
| `backend/tests/test_auth_application.py` | Modify | Deterministic current-snapshot merge without continuity claims. |
| `backend/integration_tests/test_provider_login_audit_evidence.py` | Create | Real local successful-login/Admin Audit mapping and merge proof only. |
| `backend/docs/features/authentication.md` | Modify | Task 4.2 successful-evidence/BR33 correction. |

## Interfaces / Contracts

```python
MAX_PROVIDER_AUDIT_ENTRIES = 500
MAX_PROVIDER_AUDIT_ENTRY_BYTES = 4096
MAX_PROVIDER_AUDIT_RESPONSE_BYTES = 2 + MAX_PROVIDER_AUDIT_ENTRIES * (MAX_PROVIDER_AUDIT_ENTRY_BYTES + 1)
```

Provider rows are never persisted in `authentication_audits`; strict redaction, source tags, UUID-only application correlation, nullable unsafe subjects, and at-most-once provider evidence remain unchanged.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Adapter unit | `Content-Length` at/over ceiling; chunked body at/over ceiling; truncated/invalid body; 500/501 entries; duplicate IDs | Deterministic fake private HTTPX stream; every rejection raises `ProviderUnavailable` before JSON mapping where applicable. |
| Application/API | Current-snapshot ordering, cursor filtering, UUID-only correlation, redaction, malformed cursor, atomic 503 | Existing `unittest`/FastAPI TestClient; no continuity assertion. |
| Local integration | Synthetic successful provider login, real Admin Audit read, safe mapping, and `ListAudits` merge | Local-only reset/data; excludes byte/count/duplicate/malformed boundary tests and any retention/history proof. |

## Planning Alignment (Next Phase Only)

Do not edit tasks or apply-progress in this phase. The next tasks revision MUST replace obsolete capability/retention/completeness/tie-attestation requirements in tasks **1.1**, **2.1**, and **4.1** with this bounded-snapshot contract, retain task **4.2** unchanged, and mark the old PR3 blocker in `apply-progress.md` as superseded by the approved snapshot decision.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No direct PostgreSQL Auth read, migration, grant, RPC, webhook, Log Drain, backend login endpoint, frontend work, Option C, provider change, or issue work. Rollback reverts only provider-read/merge/docs changes and leaves provider data untouched.

## Open Questions

- [ ] Follow-up: approve a failed-login source; BR33 remains partially unmet.
