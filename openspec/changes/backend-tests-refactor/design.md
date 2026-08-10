# Design: Backend Test Structure Refactor

## Technical Approach

Relocate unit tests to bounded-context packages, then to the most specific meaningful layer. This implements the delta spec while preserving `unittest`, assertions, absolute `backend.tests...` imports, production code, and the separate PostgreSQL suite. Each auto-chain slice is independently mergeable and capped at 800 reviewed lines.

## Architecture Decisions

| Decision | Alternatives / tradeoff | Choice and rationale |
|---|---|---|
| Test navigation | Global layer-first is a smaller move but scatters ownership. | Context-first, layer-second, matching ADR-004 capability packaging and context ownership. |
| Support ownership | One global fake library reduces duplication but hides context semantics. | Keep `tests/support` context-neutral; keep Auth/Access fakes local unless equivalence is proven. |
| Large test modules | Splitting every class creates churn beyond the specified topology. | Move the 600-line Auth application, 569-line Access application, and 542-line Access domain modules intact: each is already one layer. Split only mixed API setup into the specified API modules; preserve assertions. |

## Target Topology

Every shown directory is a Python package and contains `__init__.py`; future `yarn_production/` and `batch_processing/` are not created until they own tests.

```text
backend/tests/
  __init__.py  support/{__init__.py,builders.py,doubles.py,http_payloads.py,values.py}
  warehouse/{__init__.py,domain/{__init__.py,test_core_contracts.py},application/{__init__.py,test_registration.py},ports/__init__.py,adapters/{__init__.py,test_mappers.py,test_repositories.py,test_transaction.py},api/{__init__.py,test_openapi.py,test_registration_endpoint.py},runtime/{__init__.py,test_composition.py,test_database_resources.py,test_settings.py}}
  access/{__init__.py,domain/{__init__.py,test_access_domain.py,test_role_presets.py},application/{__init__.py,test_access_application.py,test_access_impact_previews.py},adapters/{__init__.py,test_access_provisioning_adapter.py},api/{__init__.py,test_access_http_authorization.py},runtime/__init__.py,support/__init__.py}
  auth/{__init__.py,domain/{__init__.py,test_auth_domain.py},application/{__init__.py,test_auth_application.py,test_auth_audit_login_events.py},adapters/{__init__.py,test_auth_adapter_provider.py,test_auth_jwt_validator.py},api/{__init__.py,test_auth_admin_authorization.py,test_auth_admin_endpoints.py,test_auth_endpoints.py},runtime/{__init__.py,test_auth_pipeline.py,test_bootstrap_command.py},support/{__init__.py,doubles.py}}
```

## Data Flow

`unittest discover` → `backend.tests.<context>.<layer>.test_*` → context-local doubles or neutral `tests.support` → production ports/adapters. No test import crosses an owning context merely to reuse a fake.

## File Changes

| Paths | Action | Description |
|---|---|---|
| `backend/tests/{warehouse,access,auth}/**` | Move/create | Context/layer packages, required `__init__.py`, and local support. |
| `backend/tests/{api,application,domain,persistence,runtime}/**`, root `test_*.py` | Delete after move | Retire old unit paths only after their replacement passes. |
| `AGENTS.md`, `backend/docs/testing/strategy.md` | Modify | Context-qualified focused commands. |

## Migration Slices

Use `F = uv run --locked --package backend python -m unittest discover -s backend/tests -v`; every slice runs `F` (252 passing) plus its focal command.

| Slice | Files / destination | Focal command |
|---|---|---|
| W1 | `domain`, `application`, `ports` → `warehouse/...` | `uv run --locked --package backend python -m unittest backend.tests.warehouse.domain.test_core_contracts -v` |
| W2 | `persistence/test_{mappers,repositories,transaction}` → `warehouse/adapters` | `uv run --locked --package backend python -m unittest backend.tests.warehouse.adapters.test_repositories -v` |
| W3 | Warehouse API modules → `warehouse/api` | `uv run --locked --package backend python -m unittest backend.tests.warehouse.api.test_registration_endpoint -v` |
| W4 | Warehouse runtime modules; retain neutral support | `uv run --locked --package backend python -m unittest backend.tests.warehouse.runtime.test_composition -v` |
| A1 | `test_access_domain`, `test_role_presets` → `access/domain` | `uv run --locked --package backend python -m unittest backend.tests.access.domain.test_access_domain -v` |
| A2 | `test_access_application`, `test_access_impact_previews` → `access/application` | `uv run --locked --package backend python -m unittest backend.tests.access.application.test_access_application -v` |
| A3 | provisioning and HTTP authorization → `access/{adapters,api}`; add empty runtime/support packages | `uv run --locked --package backend python -m unittest backend.tests.access.api.test_access_http_authorization -v` |
| AU1 | Auth domain/application/audit and verified local Auth doubles → `auth/{domain,application,support}` | `uv run --locked --package backend python -m unittest backend.tests.auth.application.test_auth_application -v` |
| AU2 | provider/JWT and all Auth API modules → `auth/{adapters,api}` | `uv run --locked --package backend python -m unittest backend.tests.auth.api.test_auth_endpoints -v` |
| AU3 | pipeline/bootstrap → `auth/runtime` | `uv run --locked --package backend python -m unittest backend.tests.auth.runtime.test_auth_pipeline -v` |

## Interfaces / Contracts

The three Auth endpoint/application copies of `InMemoryAccountRepository` and `InMemoryAuditRepository` are candidates for `auth/support/doubles.py`: their tested method surface and state transitions match. `FakeIdentityProvider`, `FakeAccessProvisioning`, and `FakeClock` remain local unless their constructor inputs, recorded state, return values, failure behavior, and every consumed protocol method match. Access `Users`, `Roles`, `Scopes`, repositories, clock, transaction, audit, and scenario helpers remain local: their method surfaces differ among application, preview, preset, and HTTP tests.

Equivalence is demonstrated only by a side-by-side protocol inventory, identical initial state and mutation/return/error semantics, and focused tests proving no consumer loses a method or semantic assertion. This is a refactor-only extraction; it introduces no production interface.

## Testing Strategy

Unit: `F` and one focused context route per slice. Integration/E2E: N/A; this change must not execute, relocate, or alter `backend/integration_tests/`. No new test framework or quality tool.

## Documentation, Risks, and Acceptance

Update `AGENTS.md` and `backend/docs/testing/strategy.md` to retain `F` and replace the focused example with `backend.tests.warehouse.domain.test_core_contracts`; document class/method suffix support. Do not alter integration instructions.

Risks: **CRITICAL** preserve RequestPipeline evidence without wiring/removal; **WARNING** fake extraction can weaken assertions, and moves can break discovery; mitigate with admission proof plus every-slice checkpoints. **INFO** Starlette/httpx warning and PGRST106 remain excluded.

Final checklist: all packages have `__init__.py`; target paths and absolute imports are present; support admission is documented; `F` reports 252; representative context-qualified class/method commands pass; `backend/integration_tests/` and production files are unchanged.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No data migration. Merge and roll back one verified slice at a time.

## Open Questions

- [ ] None; assume existing large single-layer modules remain cohesive unless implementation evidence disproves it.
