# Apply Progress: Provider Login Audit Evidence

## Work Units

- PR1 contracts/adapter (completed), including the `httpx.QueryParams` correction.
- PR2 merge/API (completed): feature-branch-chain slice following PR1; targets the immediate prior child branch when opened.

## Engram Persistence

- Topic: `sdd/provider-login-audit-evidence/apply-progress` (PR1 observation `#1258`; updated after this slice).

## Completed Tasks

- [x] 1.1 Provider-neutral success evidence contract and RED tests.
- [x] 1.2 Application/API RED tests for safe correlation, cursors, and atomic failure.
- [x] 2.1 Fail-closed Admin Audit API adapter.
- [x] 2.2 Application audit `as_of` deterministic keyset persistence.
- [x] 3.1 Cross-source merge, opaque cursor, and safe UUID correlation.
- [x] 3.2 Source-tagged HTTP page and bootstrap wiring.

## PR1 Preserved Results

- Provider evidence remains success-only, fail-closed, application-persistence-free, and uses `httpx.QueryParams` for `timestamp_to`.

## PR2 Results

- Application reads use `(occurred_at DESC, audit_id ASC)` keysets bounded by UTC `as_of`.
- `ListAudits` merges provider and application candidates by timestamp, source rank, and entry ID; malformed cursors return 422 and provider failure returns the existing 503 mapping without a partial page.
- Provider subjects are correlated only after UUID validation; absent or unsafe subjects remain nullable. Responses expose source and no provider payload.

## Work Unit Evidence

| Evidence | Result |
| --- | --- |
| RED | Before production implementation, the focused command ran 42 tests with 15 expected errors from the absent four-dependency `ListAudits` orchestration, cursor handling, and keyset API. |
| GREEN focused command | `uv run --locked --package backend python -m unittest backend.tests.test_auth_application backend.tests.api.test_auth_admin_endpoints backend.tests.api.test_auth_admin_authorization -v` — exit 0; 43 tests passed. |
| Compatibility command | `uv run --locked --package backend python -m unittest backend.tests.api.test_auth_endpoints -v` — exit 0; 10 tests passed. |
| Runtime harness | FastAPI TestClient scenarios in the focused API suite: malformed cursor 422, atomic provider-unavailable 503, source-tagged response, and `manage_access` authorization passed. No Supabase reset was run; task 4.1 owns that integration capability proof. |
| Provider adapter command | N/A — no provider adapter/contract source changed in PR2; the PR1 `QueryParams` behavior remains untouched. |
| Rollback boundary | Revert only the audit keyset port/adapter, `ListAudits`, audit HTTP page models/router/bootstrap wiring, and their focused unit/API test support. Provider adapter behavior, migrations, and unrelated worktree changes remain intact. |

## Changed Files (PR2)

- `backend/src/auth/{application/list_audits.py,ports/audit_repository.py}`
- `backend/src/auth/adapters/{persistence/audit_repository.py,http/{models.py,admin_router.py}}`
- `backend/src/bootstrap/auth_dependency.py`
- `backend/tests/test_auth_application.py`
- `backend/tests/api/{test_auth_admin_endpoints.py,test_auth_admin_authorization.py,test_auth_endpoints.py}`
- `openspec/changes/provider-login-audit-evidence/{tasks.md,apply-progress.md}`

## Slice Budget and Remaining Tasks

- PR2 implementation/test source diff: 181 additions/deletions before OpenSpec progress artifacts; within the 400-line review budget.
- [ ] 4.1 Revised bounded-stream adapter hardening and synthetic provider integration proof.
- [ ] 4.2 Documentation correction.
- [ ] 4.3 Final review/commit evidence (human controlled).

## PR3 Attempt: Integration Capability Gate (Blocked)

- CLI discovery completed from the repository root: `pnpm supabase --help`, `pnpm supabase db --help`, `pnpm supabase db reset --help`, `pnpm supabase start --help`, and `pnpm supabase stop --help`. The discovered `db reset` flags include `--local` and `--no-seed`.
- The explicitly authorized local-only command `pnpm supabase db reset --local --no-seed` completed after `pnpm supabase start` confirmed the local stack was running. No hosted command, provider change, migration, or persistent synthetic identity was created.
- A server-only synthetic capability probe against local `GET /auth/v1/admin/audit` returned HTTP 200 with a top-level JSON array (zero entries after reset). Current Supabase Auth documentation likewise defines the successful Admin Audit response only as an array of audit entries.
- The design gate requires a complete bounded response with `complete`, `has_more`, `retained_from`, echoed `timestamp_to`, stable equal-time tie evidence, and a recorded maximum. The available Admin Audit contract exposes none of those fields or a pagination/completeness proof. Therefore it cannot prove retention, completeness, or bounded retrieval/tie behavior, and the current adapter correctly fails closed rather than weakening the contract.

## PR3 Work Unit Evidence

| Evidence | Result |
| --- | --- |
| Focused integration command | Not run: no deterministic integration test was created because the provider Admin Audit capability gate failed before synthetic login setup. |
| Runtime harness | `pnpm supabase start` followed by `pnpm supabase db reset --local --no-seed` — exit 0. Local-only reset completed with no seed. Server-only Admin Audit probe — HTTP 200, JSON array, 0 entries; missing the required completeness/retention contract. |
| Focused unit/API commands | Not run after the blocking gate; PR3 made no production, unit, or API code change. PR1/PR2 evidence above remains the current passing evidence. |
| Documentation correction | Not performed: task 4.2 is held because the required task 4.1 capability proof cannot meet the design without changing its acceptance contract. The normative PRD remains untouched. |
| Rollback boundary | No implementation files changed. The local reset is isolated to the authorized local Supabase database; no synthetic rows or processes created by PR3 require cleanup. |

## PR3 Status

- Historical blocker status is preserved above. It is SUPERSEDED by the explicit human decision to use a bounded recent successful-login snapshot; it does not claim the revised implementation is complete.
- At the blocked attempt, authored implementation changed lines were 0; that progress revision added 22 authored lines, making its PR3 total 22/400. No PR3 commit was created.
- PR3 remains pending revised tasks 4.1–4.3. The revised 4.1 must harden the private GoTrue/HTTPX stream seam and prove successful-login mapping/merge without asserting provider completeness, retention, or history.

## PR3 Correction Decision

- The prior unattested-completeness PR3 blocker is SUPERSEDED, not erased: the reset, HTTP 200 bare-array probe, and missing completeness/retention evidence remain historical facts above.
- Approved decision: treat `GET /auth/v1/admin/audit` as a bounded recent snapshot of available successful-login evidence; fail closed on transport, authorization, malformed, size, truncation, invalid-body, and duplicate-ID failures.
- No provider history, retention guarantee, completeness claim, provider keyset pagination, or failed-login/BR33 completion is required by revised PR3.
- No production, unit, integration, documentation, commit, or issue work was performed by this planning revision.

## PR3 Bounded Snapshot Completion

- The obsolete completeness/retention blocker above is superseded by the approved bounded-snapshot objective; its historical probe and reset evidence are preserved unchanged.
- `IdentityProviderAdapter` now streams the private GoTrue HTTPX seam before JSON decoding, rejects a response exceeding 2,048,502 bytes, accepts at most 500 entries, and fails atomically on status, malformed/truncated body, invalid required fields, or duplicate non-empty IDs.
- The local proof creates and signs in a synthetic user, reads the bounded snapshot through the adapter, and accepts zero or one matching current entry. It intentionally makes no provider-history, retention, completeness, cross-request-continuity, or combined-endpoint claim because those properties are environment-dependent or outside the approved snapshot scope.
- §16 now describes only a bounded recent successful-login snapshot; failed-login evidence and full BR33 remain unresolved. The legacy C5 write skeleton is clarified as separate from read-only provider snapshots.

## PR3 Work Unit Evidence

| Evidence | Result |
| --- | --- |
| RED | `uv run --locked --package backend python -m unittest backend.tests.test_auth_adapter_provider -v` — expected import failure before the stream-bound constant existed. |
| Adapter GREEN | Same command — exit 0; 17 tests passed. Covers stream seam, byte ceiling at/over boundary, chunk overflow, malformed/truncated/top-level/required-field failures, 500/501, duplicate IDs, ordering, allow-list redaction, and persistence independence. |
| Application/API | `uv run --locked --package backend python -m unittest backend.tests.test_auth_application backend.tests.api.test_auth_admin_endpoints backend.tests.api.test_auth_admin_authorization backend.tests.api.test_auth_endpoints -v` — exit 0; 53 tests passed. |
| C5 compatibility | `uv run --locked --package backend python -m unittest backend.tests.test_auth_audit_login_events -v` — exit 0; 3 tests passed. |
| Local integration | Guarded local integration command — exit 0; 1 test passed. It created a synthetic user, completed a successful password login, read the Admin Audit snapshot, and deleted the identity. The assertion intentionally permits zero or one visible match; no provider-history claim is made. |
| Runtime/reset | `pnpm supabase db reset --local --no-seed` — exit 0 before the proof and again after it to remove synthetic local Auth/audit state. Local stack remains running. |
| Rollback boundary | Revert only PR3 stream admission, bounded-snapshot wording, integration/unit tests, C5 clarification, and this evidence. PR1/PR2 contracts, cursor mechanics, application persistence, and unrelated worktree files remain intact. |

## PR3 Delivery Record

- Conventional commit plan only (not created): `feat(auth): bound provider audit snapshots`.
- Changed files: `backend/src/auth/adapters/identity_provider/admin_client.py`, `backend/src/auth/ports/identity_provider.py`, `backend/src/auth/application/list_audits.py`, `backend/tests/test_auth_adapter_provider.py`, `backend/integration_tests/test_provider_login_audit_evidence.py`, `backend/docs/features/authentication.md`, `backend/src/auth/adapters/persistence/audit_repository.py`, `backend/tests/test_auth_audit_login_events.py`, and this change's `tasks.md`/`apply-progress.md`.
- PR3 authored additions and deletions: 180 lines, within the 400-line review budget.
- No hosted command, direct Auth-schema query, migration, grant, RPC, webhook, Log Drain, frontend work, issue update, branch, commit, push, or PR was created.

## Authorized Integration Merge-Proof Correction

- Scope: only `backend/integration_tests/test_provider_login_audit_evidence.py` plus this evidence record; no production code or task state changed.
- The local test now passes the real adapter's current snapshot through `ListAudits` on every run and always asserts the application entry remains in the combined page.
- When the synthetic provider login is visible, it asserts a `source: provider`, `login_succeeded` entry with UUID-safe account correlation and no operation, actor, provider-session, reason, or details leakage; a same-timestamp application entry sorts first.
- A zero-visible snapshot remains an allowed outcome and explicitly makes no provider-history or retention claim.
- Guarded integration command: exit 0; 1 test passed. Final `pnpm supabase db reset --local --no-seed` exit 0 removed synthetic local identity/audit state; stack remains running.
- Correction authored additions and deletions: 43 lines, within the 120-line limit. Rollback reverts only this integration assertion and evidence record.

## Authorized Post-Apply Timestamp Invariant Correction

- Native authority: acquire state `proceed`; orchestration token retained externally (`sha256:ff135191b2a8a385ee2381724438d90371c103e18ff54beadf17c524c47c7fe8`). One bounded correction attempt; no native operations were invoked here.
- Root cause: `AuthAuditEntry.occurred_at` was optional although every valid application and provider audit entry, the PostgreSQL schema, sorting, keyset comparison, and cursor encoding require a timestamp. The broad router `except ValueError` could also misclassify an internal timestamp invariant failure as a malformed client cursor.
- Correction: `occurred_at` and `details` are required DTO fields; the DTO rejects an absent/empty timestamp. Persistence and HTTP response contracts now preserve non-null timestamps. `InvalidAuditCursor` exclusively represents client cursor decoding failures, so malformed cursors remain `422` while internal timestamp defects follow the generic safe `500` path without a partial page.
- All 9 task checkboxes remain completed; no task scope, provider behavior, migration, integration reset, documentation, branch, commit, PR, or issue changed.

### Post-Apply Work Unit Evidence

| Evidence | Result |
| --- | --- |
| Focused test command | `uv run --locked --package backend python -m unittest backend.tests.test_auth_application backend.tests.api.test_auth_admin_endpoints backend.tests.api.test_auth_admin_authorization backend.tests.api.test_auth_endpoints -v` — exit 0; 54 tests passed. Includes the DTO missing-timestamp rejection and malformed-cursor `422` API behavior. |
| Runtime harness | FastAPI TestClient scenarios within that command — exit 0; audit endpoint cursor validation, provider-unavailable atomic `503`, source-tagged response, and authorization passed. No separate integration boundary changed; no Supabase reset run. |
| Rollback boundary | Revert only the `AuthAuditEntry` timestamp invariant, persistence/HTTP non-null typing, cursor-specific exception mapping, focused DTO test, and this correction evidence. The provider snapshot, cursor format/semantics, API success behavior, and all prior work units remain intact. |

- Correction source/test delta is within the 80-line limit; it is a single post-apply remediation work unit.
