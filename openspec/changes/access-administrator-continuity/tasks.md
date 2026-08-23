# Tasks: Access Administrator Continuity

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | Phase 2 measured: 702; total forecast: 850–1,050 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 policy/migration → PR 2 Access continuity → PR 3 Auth/composition/HTTP → PR 4 integration evidence |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Policy, runbook, guarded migration | PR 1; base = feature/tracker branch | `pnpm supabase db reset --local --no-seed` | Refuse one-admin enablement, then enable with two | Docs and continuity migration |
| 2A | Access continuity port/adapter, guards, errors | PR 2; base = PR 1 branch | `uv run --locked --package backend python -m unittest backend.tests.access.adapters.test_administrator_continuity backend.tests.access.application.test_access_application -v` | Access 3→2 succeeds; 2→1 rejects unchanged | Access port, adapter, guards, errors, tests |
| 2B | Auth lifecycle guards, composition, HTTP/errors | PR 3; base = PR 2 branch | `uv run --locked --package backend python -m unittest backend.tests.auth.application.test_auth_application backend.tests.auth.api.test_auth_admin_endpoints -v` | Disable/reset deny locally before provider calls | Auth port/use cases, bootstrap, HTTP/errors, tests |
| 3 | Isolated integration evidence | PR 4; base = PR 3 branch | `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked --package backend python -m unittest discover -s backend/integration_tests -v` | Local Supabase concurrency and isolated fixtures | Integration fixtures and tests only |

## Phase 1: Policy and Migration

- [x] 1.1 Update `docs/prd/access-control.md`, `docs/prd/auth.md`, and `docs/data-models/conceptual/access-dictionary.md` with operational-state, distinct-principal floor-two, ownership, and deletion exclusion.
- [x] 1.2 Create `docs/runbooks/administrator-recovery.md`: two-custodian ordinary approval; emergency evidence, immediate notice, closure, revocation, and review; no application bypass.
- [x] 1.3 RED: add migration integration cases for one-admin enablement refusal and two-admin enablement; prove unchanged state on refusal.
- [x] 1.4 Generate `supabase/migrations/<timestamp>_enforce_administrator_continuity.sql` with locked singleton, indexes, RLS/privilege revocations, preflight, and guarded enablement.

## Phase 2A: Access Continuity Slice (PR 2)

- [x] 2.1 RED: add `backend/tests/access/adapters/test_administrator_continuity.py` and Access application cases for inactive exclusion, distinct count, 3→2 success, 2→1 rejection, and unchanged state.
- [x] 2.2 Create `backend/src/access/ports/administrator_continuity.py` and `backend/src/access/adapters/persistence/administrator_continuity.py` with singleton locking and projected floor-two assertion.
- [x] 2.3 Update `backend/src/access/application/deactivate_access_user.py`, `replace_user_roles.py`, `adapters/access_provisioning.py`, and `domain/errors.py` for atomic guards and Access 409 semantics.

## Phase 2B: Auth, Composition, and HTTP Slice (PR 3)

- [x] 2.4 RED: add `backend/tests/auth/application/test_auth_application.py` cases for disable/reset rejection, rollback, and provider-after-durable-denial ordering.
- [x] 2.5 Update `backend/src/auth/ports/access_provisioning.py` and `application/{disable_account,reset_password}.py` to assert before local lifecycle mutation.
- [x] 2.6 Update `backend/src/bootstrap/{access_admin_dependency,auth_dependency}.py` for one shared session-backed adapter; update `backend/src/auth/domain/errors.py`.
- [x] 2.7 Update `backend/src/{auth,access}/adapters/http/` and `backend/tests/auth/api/` to preserve continuity HTTP 409 semantics without a recovery route.

## Phase 3: Isolated Integration Verification

- [x] 3.1 Replace mutable canonical-admin setup in `backend/integration_tests/test_access_control_critical.py` with per-test owned accounts/profiles/assignments; RED-test canonical fixtures unchanged.
- [x] 3.2 Extend that file with concurrent disjoint reductions: one succeeds or both serialize safely, never fewer than two operational administrators.
- [x] 3.3 Extend `backend/integration_tests/test_auth_lifecycle_local_supabase.py` for cross-context 3→2, 2→1 rollback, and provider ordering using isolated fixtures.
- [x] 3.4 Add OpenAPI/HTTP checks in `backend/tests/auth/api/` that recovery/bypass paths return 404; run focused unit and guarded integration suites.
