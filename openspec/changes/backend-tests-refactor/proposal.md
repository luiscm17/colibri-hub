# Proposal: Backend Test Structure Refactor

## Intent

Normalize unit-test navigation around bounded-context ownership while preserving assertions, `unittest`, and the isolated PostgreSQL integration suite. This removes the mixed Warehouse-layer/root Auth-Access layout and reduces unsafe duplicate doubles.

## Scope

### In Scope
- Relocate and split unit tests under context-first, layer-second packages.
- Establish shared versus context-local test-support rules.
- Preserve discovery and documented focused-test workflows through updated dotted paths and documentation.

### Out of Scope
- Production-code, behavior, dependency, pytest, coverage, lint, or fixture-framework changes.
- RequestPipeline wiring/removal; Starlette/httpx warning; PGRST106 `auth.sessions` issue.
- Any change to `backend/integration_tests/`.

## Capabilities

### New Capabilities
None — this is a test-only structural refactor.

### Modified Capabilities
None — no product requirement changes.

## Approach

Select **context-first, layer-second** over global layer-first (which weakens ownership) and source-adjacent mirroring (which breaks centralized discovery). Retain a layer only when it expresses a real test contract; split oversized modules by cohesive behavior and migrate in green checkpoints.

## Target Structure

```text
backend/tests/
  support/                         # stable technical kernel
  warehouse/{domain,application,ports,adapters,api,runtime}/
  access/{domain,application,adapters,api,runtime,support}/
  auth/{domain,application,adapters,api,runtime,support}/
  yarn_production/, batch_processing/ # created when each context gains tests
```

## Migration Rules

- Move all 12 root modules: `test_access_{application,domain,impact_previews,provisioning_adapter}`, `test_auth_{adapter_provider,application,audit_login_events,domain,jwt_validator,pipeline}`, `test_bootstrap_command`, and `test_role_presets` into their owning `access/` or `auth/` layer; `pipeline` and bootstrap tests remain `auth/runtime/`.
- Move current global Warehouse layer packages beneath `warehouse/`; retain `test_*.py`, `__init__.py`, and absolute `backend.tests...` imports.
- Run discovery after each slice. Replace the documented focused path with its context-qualified path (for example, `backend.tests.warehouse.domain.test_core_contracts`) before retiring its old location; use the same dotted module/class/method syntax.

## Support Decision

`support/` contains only stable, context-neutral builders, values, HTTP payloads, and protocol-identical doubles. Repository fakes, clocks, identity providers, and scenario builders remain context-local until method surface and state semantics are proven identical.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `backend/tests/` | Modified | Context/layer migration and support extraction |
| `backend/docs/testing/strategy.md`, `AGENTS.md` | Modified | Focused-command documentation |
| `backend/integration_tests/` | None | Remains PostgreSQL-only and separate |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Pipeline evidence is lost | Med | Preserve tests; separate auth decision |
| Fake semantics change | Med | Consolidate only proven-identical protocols |
| Imports/discovery regress | Med | Per-slice full and focused runs |
| Review overload | High | Context/layer PR slices within 800 lines |

## Rollback Plan

Revert the affected migration slice, restore prior module paths/imports, and rerun the unit suite. No schema or production rollback is required.

## Dependencies

- Separate approved authentication decision before any RequestPipeline runtime change.

## Success Criteria

- [ ] Discovery passes with unchanged test behavior and count.
- [ ] Each context has only cohesive layer packages; integration tests are untouched.
- [ ] Shared doubles meet the support rule; focused commands use documented paths.

## Proposal Question Round

User-directed assumption: preserve all current test intent, especially RequestPipeline evidence; no product-policy decision is implied by relocation.
