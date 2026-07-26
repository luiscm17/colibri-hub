# Apply Progress: Backend Capability-First Refactor v2

> **Final status:** Completed historical P0 execution evidence. Later
> persistence/API/adapter naming is superseded by
> `../align-warehouse-persistence-naming/`. The test and rollback evidence below
> remains truthful, but native review authority was corrupted/invalidated; this
> record does not claim review-gate or receipt success.

## Delivery

- Strategy: force-chained, stacked-to-main.
- Completed work units: PR1 router hierarchy; PR2 canonical Bales domain and compatibility aliases; PR3 canonical application and technology-neutral ports; PR4 canonical persistence adapters and legacy shims; PR5A canonical identity and transaction adapters with legacy aliases; PR5B canonical HTTP adapter and DI/bootstrap cutover with aliases.
- PR2, PR3, PR5B, and PR6 have separate maintainer-approved `size:exception` decisions.

## Completed Tasks

- [x] 1.1 Router hierarchy, public HTTP contract, and one-session DI.
- [x] 2.1 Corrected canonical domain identity and compatibility aliases.
- [x] 3.1 Canonical application/ports move with old→new identity aliases.
- [x] 4.1 Canonical persistence records, mappers, repositories, schema compatibility, and old→new aliases.
- [x] 5.1 PR5A canonical identity and transaction adapters with old→new aliases.
- [x] 5.2 PR5B canonical HTTP adapter, old→new HTTP aliases, and DI/bootstrap cutover.

## Final Task

- [x] 6.1 Cleanup and complete verification.

## Work Unit Evidence

| Evidence | Result |
|---|---|
| PR1 focused/full tests | Focused exited 0; 8 tests passed. Full suite exited 0; 164 tests passed. |
| PR1 runtime / rollback | TestClient covered route, slash, OpenAPI, and shared session; rollback is router/bootstrap paths. |
| PR2 focused/full tests | Focused exited 0; 76 tests passed after correction. Full suite exited 0; 170 tests passed. |
| PR2 runtime / rollback | N/A—pure domain aliases; rollback is canonical domain, legacy alias, and focused test paths. |
| PR3 initial focused/full tests | Focused suite exited 0; 26 tests passed. Full suite exited 0; 171 tests passed. |
| PR3 correction focused test | `uv run --locked python -m unittest backend.tests.test_warehouse.application.test_register_bale_reception backend.tests.test_bootstrap.test_warehouse_bale_dependency backend.tests.test_warehouse.adapters.persistence.test_warehouse_transaction -v` exited 0; 27 tests passed. |
| PR3 correction full test | `uv run --locked python -m unittest discover -s backend/tests -v` exited 0; 172 tests passed. |
| PR3 correction evidence | Shared trace proves `transaction.enter → batch.add → bales.add_all → transaction.commit`; a detail-repository exception produces `transaction.rollback` and clears the staged header, without treating in-memory staging as durable persistence. |
| PR3 runtime / rollback | N/A—application/ports are framework-free. Revert canonical application/ports, old application/ports aliases, and `backend/tests/test_warehouse/application/test_register_bale_reception.py`. |
| PR4 focused test | `uv run --locked python -m unittest backend.tests.test_warehouse.adapters.persistence.test_persistence_schema backend.tests.test_warehouse.adapters.persistence.test_bale_repository backend.tests.test_warehouse.adapters.persistence.test_warehouse_transaction -v` exited 0; 16 tests passed. SQLite confirms mapper/repository behavior and schema metadata only. |
| PR4 full test | `uv run --locked python -m unittest discover -s backend/tests -v` exited 0; 174 tests passed. |
| PR4 runtime harness | N/A—external PostgreSQL and Supabase integration are deferred to PR6 by design; no external runtime boundary changed in this slice. |
| PR4 rollback | Revert `backend/src/warehouse/bales/adapters/persistence/`, the six old persistence alias modules, and the two focused persistence tests; no schema, migration, HTTP, DI, identity, or transaction files changed. |
| PR4 scope / budget | `git diff --check` passed. Exact PR4 code/test change count: 154 additions + 221 deletions = 375; within the 400-line limit. |
| PR5A focused tests | `uv run --locked python -m unittest backend.tests.test_warehouse.adapters.identity.test_identity_generator backend.tests.test_warehouse.adapters.persistence.test_warehouse_transaction -v` exited 0; 9 tests passed. This covers canonical/legacy class identity, UUID generation, canonical protocols, commit and body rollback behavior, named constraints, and unknown `IntegrityError` propagation. |
| PR5A relevant legacy/full tests | The legacy transaction module remains covered by the focused command. `uv run --locked python -m unittest discover -s backend/tests -v` exited 0; 178 tests passed. Existing HTTP/DI consumers continued importing the old FQNs through the aliases. |
| PR5A runtime harness | N/A—no external database, HTTP, DI, schema, or migration boundary changed. Mocked transaction protocol tests cover the adapter boundary; external PostgreSQL/Supabase verification remains PR6. |
| PR5A rollback | Revert `backend/src/warehouse/bales/adapters/identity/`, `backend/src/warehouse/bales/adapters/persistence/transaction.py`, the two old adapter aliases, and the two focused test modules to restore runnable PR4. |
| PR5A scope / budget | `git diff --check` passed. Exact PR5A code/test count: 124 additions + 76 deletions = 200; within the strict 400-line budget. No `size:exception` used. Pre-existing unrelated `pyproject.toml` modification remained untouched. |
| PR5B RED / focused tests | RED failed before production code with missing canonical HTTP router. Focused suite exited 0; 55 tests passed. |
| PR5B runtime / full tests | TestClient verified the historical payload/response, `reception_id`, 201, one OpenAPI POST path, slash 307, and 409/422/500 envelopes. Full suite exited 0; 181 tests passed. |
| PR5B rollback / budget | Revert canonical HTTP, seven alias modules, bootstrap cutover, warehouse HTTP composition, and PR5B tests. Exact code/test count: 499 additions + 353 deletions = 852, under the separately approved bounded `size:exception`. |
| PR6 budget preflight | Removing the identified old source aliases/facades alone is 428 deleted lines: `warehouse.{domain,application,ports}` old surfaces, `warehouse.adapters.{identity,persistence,http}` aliases, and raw-material package shims. This excludes required canonical test/import updates and canonical temporary property/constructor alias removal. It exceeds PR6's strict 400 changed-line budget. No source/test changes or verification commands were run. |

## Notes

- At this P0 work unit, canonical records retained `raw_material_receptions`, `raw_material_bales`, `reception_id`, named constraints, `Decimal`, and timezone-aware `datetime` metadata; the later alignment change supersedes those physical/API names.
- The batch repository adds and flushes the header before the existing application order calls the Bale repository. PR5A moves transaction/error translation unchanged into the canonical capability adapter.
- PR6 is complete under the PR6-only `size:exception`; rollback is limited to cleanup seams.
- No schema/migration, P1 behavior, staging, commit, push, or PR operation was performed.

## PR6 Resumed Evidence

- Maintainer approved `size:exception` for PR6 only. The cleanup removed all tracked temporary `warehouse.*.raw_material` alias modules and old `warehouse.{domain,application,ports}` plus identity/persistence facades; it retained only historical transport/persistence schema vocabulary.
- Focused affected unit command exited 0; 137 tests passed: `uv run --locked python -m unittest backend.tests.test_warehouse.bales.domain.test_raw_material_batch backend.tests.test_warehouse.domain.test_bale backend.tests.test_warehouse.domain.test_bale_reception backend.tests.test_warehouse.domain.test_value_objects backend.tests.test_warehouse.application.test_register_bale_reception backend.tests.test_warehouse.adapters.identity.test_identity_generator backend.tests.test_warehouse.adapters.persistence.test_persistence_schema backend.tests.test_warehouse.adapters.persistence.test_warehouse_transaction backend.tests.test_warehouse.adapters.http.raw_material.test_bale_router backend.tests.test_warehouse.adapters.http.raw_material.test_bale_reception_http_models backend.tests.test_warehouse.bales.adapters.http.test_canonical_http_adapter backend.tests.test_bootstrap.test_http_application -v`.
- Full unit command exited 0; 176 tests passed: `uv run --locked python -m unittest discover -s backend/tests -v`.
- PostgreSQL integration command exited 0; 11 tests passed against the required loopback URL.
- ASGI startup/TestClient/OpenAPI command exited 0: exact path list `['/api/v1/warehouse/bales']`, malformed POST 422, trailing-slash POST 307.
- Static import audit found no `warehouse.{domain,application,ports,adapters}.raw_material`, old identity, or old transaction imports. Canonical packages and ASGI factory import successfully.
- `git diff --check` exited 0. PR6 backend line accounting is 144 additions + 654 deletions = 798, permitted by the PR6-only `size:exception`. Protected migration/schema diff is empty; the pre-existing `pyproject.toml` modification remains outside the PR6 count.
- Supabase CLI 2.109.1 was available through the NVM login shell. `zsh -lic 'pnpm supabase status'` confirmed local services running, with warnings that imgproxy, edge-runtime, and pooler were stopped. `zsh -lic 'pnpm supabase db reset --local --no-seed'` exited 0 and applied `20260722130455_create_raw_material_reception_storage.sql`. `zsh -lic 'pnpm supabase migration list --local'` exited 0 and showed local and remote `20260722130455` applied. The required PostgreSQL integration suite was rerun after reset and exited 0; 11 tests passed. Task 6.1 is complete.

## PR6 Cleanup Correction Evidence

- Removed dead `RegisterRawMaterialBatch._reception_repository` and `_warehouse_transaction` assignments; canonical `_raw_material_batch_repository` and `_transaction` remain.
- Moved the application suite to `backend/tests/test_warehouse/bales/application/test_register_raw_material_batch.py`, renamed its suite/fakes to canonical vocabulary, and removed the obsolete application test package.
- Moved the former BaleReception domain suite into the canonical `backend/tests/test_warehouse/bales/domain/test_raw_material_batch.py`, merged it with the pre-existing batch suite without dropping assertions, and removed the obsolete file.
- Focused moved-suite command exited 0; 33 tests passed. Full unit command exited 0; 176 tests passed. PostgreSQL integration exited 0; 11 tests passed. ASGI TestClient/OpenAPI smoke exited 0 with one POST path, 422 malformed request, and 307 trailing slash.
- Static audit found no legacy import FQNs, dead legacy attributes, `RegisterBaleReception`, or either obsolete test-file path. `git diff --check` passed; no migration/schema diff. Updated backend PR6 count is 210 additions + 1,176 deletions = 1,386 under the approved PR6-only exception.

## PR6 Final Test Cleanup Evidence

- Removed only the obsolete empty `test_returns_correct_total_net_weight`; no total-net-weight behavior was introduced or restored.
- Canonical application suite exited 0; 17 tests passed. Full backend unit suite exited 0; 175 tests passed. `git diff --check` exited 0.
- Existing Supabase reset/migration, PostgreSQL integration, and ASGI evidence remains applicable because this change is test-only.
- Final authored backend accounting includes the untracked canonical application test file: 634 additions (210 tracked + 424 untracked) + 1,176 deletions = 1,810 changed lines, covered by the PR6-only `size:exception`.

## PR5 Budget Gate

- At that checkpoint, the reverted complete PR5 prototype was superseded by the PR5A/PR5B split. PR5A was complete and PR5B remained pending until separate approval; later evidence above records PR5B completion.
- The prior complete prototype measured 960 additions plus deletions across its intended code and focused test paths, so it was reverted before sliced implementation. Its HTTP/DI work was pending at that checkpoint and was completed later as recorded above.
- No schema, migration, P1 behavior, staging, commit, push, PR, or Supabase change was made in PR5A.
