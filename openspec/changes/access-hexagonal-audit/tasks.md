# Tasks: Access Module Hexagonal/DDD Audit

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~600 (4 PRs × ~150 each) |
| 400-line budget risk | Low (per-PR; each < 200) |
| Chained PRs recommended | Yes |
| Suggested split | PR1 → PR2 → PR3 → PR4 |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Domain enrichment — behavior methods + invariants | PR1 → `back/access-control-administration` | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` | N/A — pure refactor, no runtime scenario | Revert PR1 branch; entities revert to anemic |
| 2 | Port precision + shared identity relocation | PR2 → PR1 branch | Same unit test command | N/A — import relocation, no new runtime path | Revert PR2; ports stay untyped, identity stays in warehouse |
| 3 | Adapter type safety — eliminate `# type: ignore` | PR3 → PR2 branch | Integration: `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked --package backend python -m unittest discover -s backend/integration_tests -v` | N/A — type narrowing, no behavioral change | Revert PR3; ignores return |
| 4 | Bootstrap typing — `AdminUseCases` container | PR4 → PR3 branch | Same unit test command | N/A — composition root wiring only | Revert PR4; dict provider returns |

## Phase 1: Domain Enrichment (PR1)

- [x] 1.1 Add `deactivate(*, at)` and `activate(*, at)` to `backend/src/access/domain/users.py` with idempotency + version bump
- [x] 1.2 Add `Role.grant_permission(p)` with duplicate guard in `backend/src/access/domain/roles.py`
- [x] 1.3 Extract `Assignment.revoke(by, reason, at)` with invariant guards in `roles.py`
- [x] 1.4 Add `Scope.activate()/deactivate()` behavior in `backend/src/access/domain/scopes.py`
- [x] 1.5 Update `backend/src/access/application/*` use cases to call entity behavior instead of inline mutation
- [x] 1.6 Update test factories/assertions for new entity API

## Phase 2: Port Precision + Shared Identity (PR2)

- [x] 2.1 Create `backend/src/shared/__init__.py` and `backend/src/shared/identity.py` with `AuthenticatedIdentity` + `IdentityResolver`
- [x] 2.2 Create `backend/src/access/domain/audit.py` with `AccessAuditEntry` read model
- [x] 2.3 Create `backend/src/access/ports/assignments.py` with `AssignmentRepository` protocol
- [x] 2.4 Modify `backend/src/access/ports/repositories.py` — type `list_recent` return, remove assignment methods
- [x] 2.5 Update `backend/src/warehouse/bales/ports/authorization.py` to re-export from `shared`
- [x] 2.6 Update imports in `access/adapters/http/router.py` and `bootstrap/http_application.py` to use `shared.identity`

## Phase 3: Adapter Type Safety (PR3)

- [x] 3.1 Implement `AssignmentRepositoryAdapter` in `backend/src/access/adapters/persistence/repositories.py`
- [x] 3.2 Map audit query to `AccessAuditEntry` in the same adapter; drop app-DTO import
- [x] 3.3 Type `delivery_date` guard in `backend/src/warehouse/bales/adapters/persistence/bale_repository.py` — remove 2 ignores
- [x] 3.4 Type provider row in `backend/src/auth/adapters/identity_provider/admin_client.py` — remove 1 ignore
- [x] 3.5 Add `ApplicationSettings.from_environment()` factory in `backend/src/infra/configuration/application_settings.py` — remove 2 ignores

## Phase 4: Bootstrap Typing (PR4)

- [x] 4.1 Create frozen `AdminUseCases` dataclass in `backend/src/access/application/` or `bootstrap/`
- [x] 4.2 Modify `backend/src/bootstrap/access_admin_dependency.py` to return `AdminUseCases`
- [x] 4.3 Update `backend/src/access/adapters/http/router.py` to consume typed container
- [x] 4.4 Run full unit + integration suites — confirm zero `# type: ignore` in `backend/src/`
