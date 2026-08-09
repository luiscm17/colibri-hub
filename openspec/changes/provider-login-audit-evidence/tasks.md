# Tasks: Provider Login Audit Evidence

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 240–360 authored lines (PR3) |
| 400-line budget risk | Low |
| Chained PRs recommended | Yes |
| Suggested split | Existing PR1 → PR2 → PR3 |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Low

### Feature-Branch Chain

Tracker accumulates integration; PR1 targets tracker, later children target the immediate prior branch, and only tracker merges to `main`.

### Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Provider contract, redaction, capability gate | PR 1 | `uv run --locked --package backend python -m unittest backend.tests.test_auth_adapter_provider -v` | Admin API synthetic probe; N/A if gate unavailable | provider port/adapter and its tests |
| 2 | Atomic cross-source merge and HTTP contract | PR 2 | `uv run --locked --package backend python -m unittest backend.tests.test_auth_application backend.tests.api.test_auth_admin_endpoints backend.tests.api.test_auth_admin_authorization -v` | FastAPI TestClient scenarios | list-audits, repository, HTTP, bootstrap changes |
| 3 | Bounded adapter hardening, local proof, and docs correction | PR 3 | `uv run --locked --package backend python -m unittest backend.tests.test_auth_adapter_provider backend.integration_tests.test_provider_login_audit_evidence -v` | `pnpm supabase --help`; then approved local reset and synthetic successful-login merge scenario | adapter/tests, integration test, and §16 wording; revert without PR1/PR2 |

## Phase 1: Contracts and RED Tests

- [x] 1.1 Establish the initial success-only `ProviderLoginAuditEvidence` contract and RED tests in `backend/src/auth/ports/identity_provider.py` and `backend/tests/test_auth_adapter_provider.py`; streaming bounds and duplicate rejection remain for 4.1.
- [x] 1.2 Add failing tests in `backend/tests/test_auth_application.py`, `backend/tests/api/test_auth_admin_endpoints.py`, and `backend/tests/api/test_auth_admin_authorization.py` for UUID-only correlation, nullable subjects, equal-time ordering, malformed cursor `422`, and atomic `503 authentication_provider_unavailable`.

## Phase 2: Provider and Persistence GREEN

- [x] 2.1 Complete the initial fail-closed adapter in `backend/src/auth/adapters/identity_provider/admin_client.py`; revised stream, 500/501, malformed-body, and duplicate-ID hardening remains 4.1.
- [x] 2.2 Update `backend/src/auth/ports/audit_repository.py` and `backend/src/auth/adapters/persistence/audit_repository.py` for `as_of` plus deterministic keyset predicates; prove application rows remain unchanged and ordered.

## Phase 3: Merge and HTTP Wiring

- [x] 3.1 Implement `ListAudits` in `backend/src/auth/application/list_audits.py` with UTC `as_of`, opaque base64url cursor `{v,as_of,occurred_at,source_rank,entry_id}`, UUID-safe `find_by_subject`, rank `(application=0, provider=1)`, page-size-plus-one merge, and no partial result on provider failure.
- [x] 3.2 Update `backend/src/auth/adapters/http/models.py`, `backend/src/auth/adapters/http/admin_router.py`, and `backend/src/bootstrap/auth_dependency.py` for source-tagged nullable responses and `manage_access`; pass API tests for authorization, redaction, pagination, exhaustion, and 503 atomicity.

## Phase 4: Integration, Docs, and Review Evidence

- [x] 4.1 Add RED coverage, then harden `backend/src/auth/adapters/identity_provider/admin_client.py` and `backend/tests/test_auth_adapter_provider.py` at the private GoTrue/HTTPX stream seam: enforce the pre-decode byte ceiling; reject HTTP 500/501 entry boundaries, oversized/truncated/invalid bodies, and duplicate IDs. Add local synthetic Admin Audit successful-login mapping and combined-endpoint proof in `backend/integration_tests/test_provider_login_audit_evidence.py`; assert no completeness, retention, or history.
- [x] 4.2 Correct `backend/docs/features/authentication.md` §16 for a bounded recent successful-login snapshot; preserve the normative PRD and state failed-login evidence/BR33 remain unresolved. Inspect only conflicting active C5 claims, never archives.
- [x] 4.3 Record the revised PR3 Conventional Commit plan, focused/runtime results or N/A, and rollback boundary; run planned commands and attach evidence. Do not commit or update issues.
