# Tasks: Backend Test Structure Refactor

## Forecast

| Slice | Estimate | Focus |
| --- | ---: | --- |
| W1 | 80–140 | Foundation |
| W2–W4 | 100–180 each | Warehouse layers |
| A1–A3 | 120–220 each | Access |
| AU1–AU3 | 140–260 each | Auth |
| Docs/acceptance | 40–80 | Docs |
| **Total** | **1,420–2,380** | **Over 800** |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

`F = uv run --locked --package backend python -m unittest discover -s backend/tests -v`. One mergeable slice per PR; select chain strategy before branches. Every slice requires `F` + focal command and 252 passes.

## Suggested Work Units

| Unit | PR | Focused command | Harness | Rollback |
| --- | --- | --- | --- | --- |
| W1–W4 | 1–4 | Design focal | N/A: unit-only | Revert slice |
| A1–A3 | 5–7 | Design focal | N/A: unit-only | Revert slice |
| AU1–AU3 | 8–10 | Design focal | N/A: unit-only | Revert slice |
| Docs/acceptance | 11 | Warehouse focal | N/A: docs | Revert docs |

## Warehouse (W1–W4)

- [x] 1.1 **W1:** Create `warehouse/{domain,application,ports}/__init__.py`; move `domain/test_core_contracts.py`, `application/test_registration.py`, and `ports`; delete old packages. Verify `F` + `backend.tests.warehouse.domain.test_core_contracts`; done at 252 passes and absolute imports.
- [x] 1.2 **W2:** Create `warehouse/adapters`; move `persistence/test_{mappers,repositories,transaction}.py`; delete `persistence/`. Verify `F` + `backend.tests.warehouse.adapters.test_repositories`; done when assertions pass.
- [x] 1.3 **W3:** Move `api/test_{openapi,registration_endpoint}.py` to `warehouse/api/`; create marker and delete old copies. Verify `F` + `backend.tests.warehouse.api.test_registration_endpoint`; done when assertions pass.
- [x] 1.4 **W4:** Move `runtime/test_{composition,database_resources,settings}.py` to `warehouse/runtime/`; retain neutral `support/`. Verify `F` + `backend.tests.warehouse.runtime.test_composition`; done when runtime contracts pass.

## Access (A1–A3)

- [x] 2.1 **A1:** Create `access/domain/`; move root `test_access_domain.py` and `test_role_presets.py`; delete originals. Verify `F` + `backend.tests.access.domain.test_access_domain`; done when assertions pass.
- [x] 2.2 **A2:** Create `access/application/`; move root `test_access_application.py` and `test_access_impact_previews.py`; delete originals. Verify `F` + `backend.tests.access.application.test_access_application`; done when doubles retain semantics.
- [x] 2.3 **A3:** Create `access/{adapters,api,runtime,support}/`; move provisioning to adapters and HTTP authorization to api; delete old copies. Verify `F` + `backend.tests.access.api.test_access_http_authorization`; done when markers exist and integration tests stay untouched.

## Authentication (AU1–AU3)

- [x] 3.1 **AU1:** Create `auth/{domain,application,support}/`; move auth domain/application/audit modules; extract only proven-equivalent account/audit doubles; delete originals. Verify `F` + `backend.tests.auth.application.test_auth_application`; done when protocol/state is preserved.
- [x] 3.2 **AU2:** Create `auth/{adapters,api}/`; move provider/JWT and auth API modules from root/`api/`; delete old paths. Verify `F` + `backend.tests.auth.api.test_auth_endpoints`; done when imports/assertions pass.
- [x] 3.3 **AU3:** Create `auth/runtime/`; move root `test_auth_pipeline.py` and `test_bootstrap_command.py`; delete copies, without production wiring/removal. Verify `F` + `backend.tests.auth.runtime.test_auth_pipeline`; done when evidence remains.

## Documentation and Acceptance

- [x] 4.1 Update `AGENTS.md` and `backend/docs/testing/strategy.md` with `F`, the Warehouse focal path, and suffix guidance; preserve integration commands. Verify `F` + documented focal command; done when routes match.
- [x] 4.2 Confirm every target package has `__init__.py`, imports are absolute, exactly 252 unit tests pass, and no production or `backend/integration_tests/` diff exists. Verify `F` + auth runtime focal; done at acceptance.

## Dependencies

W1 precedes W2–W4. A1–A3 are independent; AU1–AU3 are independent. Acceptance follows all slices. No RequestPipeline, warning, PGRST106, production, or integration changes.
