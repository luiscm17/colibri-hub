# Apply Progress: Backend Test Structure Refactor

## Status
- [x] 1.1 **W1:** Moved Warehouse domain and application tests under `backend.tests.warehouse`; created the empty Warehouse ports package; removed the superseded `domain/` and `application/` test packages.
- [x] 1.2 **W2:** Moved Warehouse persistence adapter tests to `backend.tests.warehouse.adapters`; created the adapters package and removed the superseded tracked `persistence/` package files.
- [x] 1.3 **W3:** Relocated Warehouse API tests to `backend.tests.warehouse.api`, retained their assertions, and made the relocated `warehouse.adapters` test package extend its path so discovery resolves the production `warehouse.adapters.http` subpackage.
- [x] 1.4 **W4:** Relocated Warehouse runtime tests to `backend.tests.warehouse.runtime`, preserved their assertions and absolute production imports, and adjusted only the moved entrypoint test's relative `main.py` lookup for its deeper package location.
- [x] 2.1 **A1:** Moved root Access domain and role-preset tests to `backend.tests.access.domain`, created the required Access package markers, and removed the superseded root modules.
- [x] 2.2 **A2:** Moved root Access application and impact-preview tests to `backend.tests.access.application`, created the required path-extending package marker, and removed the superseded root modules without changing local doubles.
- [x] 2.3 **A3:** Moved Access provisioning and HTTP authorization tests to `backend.tests.access.adapters` and `backend.tests.access.api`; created the required empty runtime/support packages and deleted their superseded copies.
- [x] 3.1 **AU1:** Moved Auth domain, application, and audit test modules to `backend.tests.auth.{domain,application}`; created the required markers and deleted superseded root modules.
- [x] 3.2 **AU2:** Moved provider/JWT adapter tests and all Auth API tests to `backend.tests.auth.{adapters,api}`; created required markers and deleted their superseded root/API paths.
- [x] 3.3 **AU3:** Moved Auth pipeline and bootstrap-command tests to `backend.tests.auth.runtime`; created the required runtime marker and deleted the superseded root modules without modifying production wiring.
- [x] 4.1 **Docs:** Updated the canonical full unit command, Warehouse focused path, and test naming/package guidance in `AGENTS.md` and `backend/docs/testing/strategy.md`; integration commands were preserved.
- [x] 4.2 **Acceptance:** Confirmed the required context-first, layer-second package markers and target test modules, retained absolute `backend.tests...` imports, and verified the required full and Auth runtime commands.

## Mode and Delivery
- Mode: Standard (`strict_tdd: false`)
- Delivery: `auto-chain`, `feature-branch-chain`
- Work-unit boundary: W1 only; the child PR targets the feature/tracker branch and contains only the Warehouse foundation relocation.
- Work-unit boundary: W2 only; the child PR targets the W1 branch and contains only Warehouse adapter-test relocation.
- Work-unit boundary: W3 only; the child PR targets the W2 branch and contains the existing Warehouse API relocation plus the test-package compatibility fix required for discovery.
- Work-unit boundary: W4 only; the child PR targets the W3 branch and contains only Warehouse runtime-test relocation.
- Work-unit boundary: A1 only; the next child PR targets the W4 branch and contains only the Access domain and role-preset test relocation.
- Work-unit boundary: A2 only; the next child PR targets the A1 branch and contains only the Access application and impact-preview test relocation.
- Work-unit boundary: A3 only; the next child PR targets the A2 branch and contains only the Access adapter/API test relocation and required empty package markers.
- Work-unit boundary: AU1 only; the next child PR targets the A3 branch and contains only the Authentication domain/application/audit test relocation and required local package markers.
- Work-unit boundary: AU2 only; the next child PR targets the AU1 branch and contains only Authentication adapter/API test relocation and required package markers.
- Work-unit boundary: AU3 only; the next child PR targets the AU2 branch and contains only Authentication runtime-test relocation and its required package marker.
- Work-unit boundary: 4.2 acceptance only; the next child PR targets the 4.1 documentation branch and contains only SDD task/progress acceptance evidence. No code, test, migration, or documentation content was changed by this unit.

## Work Unit Evidence

### W1 — Warehouse foundation
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.warehouse.domain.test_core_contracts -v` — exit 0; 4 tests passed. |
| Full unit check and exact result | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: W1 is a unit-test package relocation with no runtime boundary; integration tests are explicitly out of scope. |
| Rollback boundary | Revert `backend/tests/warehouse/`, restore `backend/tests/domain/` and `backend/tests/application/`, and reset this task checkbox; no production or integration behavior is affected. |

### W2 — Warehouse adapters
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.warehouse.adapters.test_repositories -v` — exit 0; 2 tests passed. |
| Full unit check and exact result | Originally blocked by package shadowing; the W3 full-unit checkpoint now exits 0 with 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: W2 is a unit-test package relocation with no runtime boundary; integration tests are explicitly out of scope and unchanged. |
| Rollback boundary | Revert `backend/tests/warehouse/adapters/`, restore `backend/tests/persistence/{__init__.py,test_mappers.py,test_repositories.py,test_transaction.py}`, and reset task 1.2; no production or integration behavior is affected. |

### W3 — Warehouse API and discovery compatibility
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.warehouse.api.test_registration_endpoint -v` — exit 0; 5 tests passed. |
| Full unit check and exact result | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: W3 is a unit-test package relocation with no runtime boundary; integration tests are explicitly out of scope. |
| Rollback boundary | Revert the compatibility extension in `backend/tests/warehouse/adapters/__init__.py`, W3 API relocation files in `backend/tests/warehouse/api/`, and restore `backend/tests/api/{test_openapi.py,test_registration_endpoint.py}`; no production, integration, Access/Auth, runtime, or shared-support file is affected. |

### W4 — Warehouse runtime
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.warehouse.runtime.test_composition -v` — exit 0; 4 tests passed. |
| Full unit check and exact result | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: W4 only relocates unit tests; integration tests are explicitly out of scope and were not run. |
| Rollback boundary | Remove `backend/tests/warehouse/runtime/`, restore `backend/tests/runtime/{test_composition.py,test_database_resources.py,test_settings.py}`, and reset task 1.4; no production, integration, Access/Auth, or shared-support behavior is affected. |

### A1 — Access domain and role presets
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.access.domain.test_access_domain -v` — exit 0; 56 tests passed. |
| Full unit check and exact result | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: A1 is a unit-test package relocation with no runtime boundary; `backend/integration_tests/` is explicitly out of scope and unchanged. |
| Rollback boundary | Remove `backend/tests/access/`, restore `backend/tests/{test_access_domain.py,test_role_presets.py}`, and reset task 2.1; no production, integration, Warehouse, or other Access-test behavior is affected. |

### A2 — Access application and impact previews
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.access.application.test_access_application -v` — exit 0; 22 tests passed. |
| Full unit check and exact result | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: A2 is a unit-test package relocation with no runtime boundary; `backend/integration_tests/` is explicitly out of scope and unchanged. |
| Rollback boundary | Remove `backend/tests/access/application/`, restore `backend/tests/{test_access_application.py,test_access_impact_previews.py}`, and reset task 2.2; no production, integration, Warehouse, A1, or other Access-test behavior is affected. |

### A3 — Access adapters and API
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.access.api.test_access_http_authorization -v` — exit 0; 4 tests passed. |
| Full unit check and exact result | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: A3 is a unit-test package relocation with no runtime boundary; `backend/integration_tests/` is explicitly out of scope and unchanged. |
| Rollback boundary | Remove `backend/tests/access/{adapters,api,runtime,support}/`, restore `backend/tests/test_access_provisioning_adapter.py` and `backend/tests/api/test_access_http_authorization.py`, and reset task 2.3; no production, integration, Warehouse, A1, or A2 behavior is affected. |

### AU1 — Authentication domain, application, and audit
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.auth.application.test_auth_application -v` — exit 0; 29 tests passed. |
| Full unit check and exact result | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: AU1 is a unit-test package relocation with no runtime boundary; `backend/integration_tests/` is explicitly out of scope and unchanged. |
| Rollback boundary | Remove `backend/tests/auth/{domain,application,support}/`, restore `backend/tests/{test_auth_domain.py,test_auth_application.py,test_auth_audit_login_events.py}`, and reset task 3.1; no production, integration, Warehouse, Access, API, adapter, or runtime-test behavior is affected. |

### AU2 — Authentication adapters and API
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.auth.api.test_auth_endpoints -v` — exit 0; 10 tests passed. |
| Full unit check and exact result | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: AU2 is a unit-test package relocation with no runtime boundary; `backend/integration_tests/` is explicitly out of scope and unchanged. |
| Rollback boundary | Remove `backend/tests/auth/{adapters,api}/`, restore `backend/tests/{test_auth_adapter_provider.py,test_auth_jwt_validator.py}` and `backend/tests/api/{test_auth_admin_authorization.py,test_auth_admin_endpoints.py,test_auth_endpoints.py}`, and reset task 3.2; no production, integration, Warehouse, Access, AU1, or Auth runtime-test behavior is affected. |

### AU3 — Authentication runtime
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.auth.runtime.test_auth_pipeline -v` — exit 0; 12 tests passed. |
| Full unit check and exact result | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: AU3 is a unit-test relocation with no runtime boundary; `backend/integration_tests/` is explicitly out of scope and unchanged. |
| Rollback boundary | Remove `backend/tests/auth/runtime/`, restore `backend/tests/{test_auth_pipeline.py,test_bootstrap_command.py}`, and reset task 3.3; no production, integration, Warehouse, Access, AU1, or AU2 behavior is affected. |

### 4.1 — Documentation
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.warehouse.domain.test_core_contracts -v` — exit 0; 4 tests passed. |
| Full unit check and exact result | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: this work unit changes documentation only and has no runtime boundary; integration commands are preserved and `backend/integration_tests/` is out of scope. |
| Rollback boundary | Revert the documentation-only changes in `AGENTS.md` and `backend/docs/testing/strategy.md`, then reset task 4.1; no test, source, migration, production, or integration behavior is affected. |

### 4.2 — Acceptance
| Evidence | Result |
| --- | --- |
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.auth.runtime.test_auth_pipeline -v` — exit 0; 12 tests passed. |
| Full unit check and exact result | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 252 tests passed. |
| Runtime harness command/scenario and exact result | N/A: acceptance verifies a unit-test topology refactor with no runtime boundary; `backend/integration_tests/` is explicitly out of scope, unmodified, and its documented command remains preserved. |
| Rollback boundary | Revert only this 4.2 acceptance entry in `openspec/changes/backend-tests-refactor/{tasks.md,apply-progress.md}` and reset task 4.2; no code, tests, migrations, production, integration, or documentation content is affected. |

## Discovery Notes
- `unittest discover -s backend/tests` imports `warehouse` as a top-level test package. Both `backend/tests/warehouse/__init__.py` and its relocated `adapters/__init__.py` must extend their package paths so imports can traverse to production `warehouse.adapters.http` in `backend/src`.
- A1 likewise needs both `backend/tests/access/__init__.py` and `backend/tests/access/domain/__init__.py` to extend their package paths. Otherwise the test package shadows production `access.domain`, causing `ModuleNotFoundError` during discovery.
- A2 likewise requires `backend/tests/access/application/__init__.py` to extend its package path so discovery resolves production `access.application` submodules rather than the relocated test package.
- AU1 likewise requires `backend/tests/auth/__init__.py` and the nested `domain` and `application` markers to extend their package paths so discovery resolves production `auth.domain` and `auth.application` submodules rather than the relocated test packages. Account/audit doubles remain in the moved application module because the endpoint duplicates belong to AU2; extraction is not required for AU1 and would expand its boundary.
- AU2 requires `backend/tests/auth/adapters/__init__.py` to extend its package path so discovery resolves production `auth.adapters.identity_provider`; `auth/api/__init__.py` is a normal test-package marker.
- AU3 uses the existing path-extending `backend/tests/auth/__init__.py`; its nested runtime package is a normal test-package marker because no production `auth.runtime` submodules are imported.

## Scope Checks
- `git diff --exit-code` and `git diff --cached --exit-code` confirmed no changes under `backend/src/`, `backend/integration_tests/`, or Warehouse test paths from this A1 work unit.
- A2 changed only `backend/tests/access/application/` and the two superseded root Access application modules; A1 files remain unchanged.
- A3 changed only `backend/tests/access/{adapters,api,runtime,support}/`, `backend/tests/test_access_provisioning_adapter.py`, and `backend/tests/api/test_access_http_authorization.py`; `git diff --exit-code -- backend/src backend/integration_tests` passed and neither path has staged or untracked changes.
- W1–W4 remain committed as `c246bae`; A1 was not committed, pushed, or used to acquire a second native attempt.
- AU1 changed only `backend/tests/auth/{__init__.py,domain/,application/,support/}` and the three superseded root Auth modules; `git diff --exit-code -- backend/src backend/integration_tests` passed, and W1–W4 (`c246bae`) plus A1–A3 (`da35753`) remain committed and unchanged. No commit, push, or additional native attempt was made.
- AU2 changed only `backend/tests/auth/{adapters/,api/}` plus its five superseded Auth test paths; `git diff --exit-code -- backend/src backend/integration_tests` passed. W1–W4 (`c246bae`), A1–A3 (`da35753`), and AU1 (`a764214`) remain unchanged. No commit, push, or additional native attempt was made.
- AU3 changed only `backend/tests/auth/runtime/` and its two superseded root Auth test modules; focused pipeline tests passed 12/12 and full discovery passed 252/252. `git diff --exit-code -- backend/src backend/integration_tests`, cached equivalent, and untracked-path checks passed. W1–W4 (`c246bae`), A1–A3 (`da35753`), AU1 (`a764214`), and staged AU2 work remain unchanged. No commit, push, or additional native attempt was made.
- Acceptance confirmed all 23 required package markers under `backend/tests/{support,warehouse,access,auth}` are present, required target modules are in their context/layer paths, and no root `test_*.py` modules remain. No relative imports were found in `backend/tests/**/*.py`; retained test-support imports use absolute `backend.tests...` paths. Empty legacy package directories contain no relocated test modules. `git status --porcelain -- backend/src backend/integration_tests`, unstaged/staged scoped diffs, and untracked-path checks are empty. `AGENTS.md` and `backend/docs/testing/strategy.md` both retain the guarded `TEST_DATABASE_URL` integration command and discovery invocation.

## Remaining Tasks
- [x] 3.1 AU1 — Authentication domain, application, and audit
- [x] 3.2 AU2 — Authentication adapters and API
- [x] 3.3 AU3 — Authentication runtime
- [x] 4.1 Documentation
- [x] 4.2 Acceptance
