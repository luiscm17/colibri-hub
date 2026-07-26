# Proposal: Rebuild Backend Test Suite

## Intent

Replace the deleted legacy backend suite with fresh `unittest` evidence of current Warehouse behavior. Tests specify current contracts; they do not restore, port, or preserve legacy behavior. OpenSpec is planning evidence, not runtime proof.

## Scope

### Goals
- Rebuild deterministic unit, adapter, ASGI/OpenAPI, bootstrap, and guarded PostgreSQL contracts for `warehouse.bales`.
- Revalidate and rewrite current PostgreSQL test/support locations from current physical contracts.
- Preserve inward dependency boundaries and current HTTP, settings, transaction, and security behavior.

### Non-Goals
- No legacy assertion reuse, deleted-test Git/history content, `.kiro`, failed-refactor memories/artifacts, framework/tooling change, coverage target/tool, network, production DB, or unrelated refactor.
- Cache cleanup is separate operational housekeeping.

## Source of Truth and Freshness

Authority order: current production/runtime behavior; PRD; architecture/domain; DB dictionary and current migration for PostgreSQL; current OpenSpec contracts; AGENTS/dev guides. Existing current integration files are rewrite candidates only: their assertions are not source authority. “Fresh” excludes deleted tests, Git/history contents, old assertions, `.kiro`, and failed-refactor memories/artifacts.

## Capabilities

### New Capabilities
None — this rebuild specifies existing behavior.

### Modified Capabilities
None — no product requirement changes are proposed.

## Approach

Taxonomy: fast domain/application units with fakes; adapter contracts; injected ASGI/OpenAPI contracts; small PostgreSQL-only integration proof. SQLite may prove only dialect-neutral behavior; PostgreSQL alone proves constraints, diagnostics, RLS/ACL, FK actions, timezone, Decimal, and transactions. Use explicit builders, fixed aware times, `Decimal` literals, deterministic identities, injected seams, isolated cleanup, and only guarded `TEST_DATABASE_URL` local Supabase loopback access.

## Delivery

`5730050 test(backend): remove legacy test suite` is an approved one-time deletion-only `size:exception` prerequisite: it is neither a fresh slice nor green evidence. Six independently green, stacked-to-`main` slices follow, each at most 399 changed lines:
1. Domain/application.
2. Persistence adapters.
3. HTTP/OpenAPI/errors.
4. Infrastructure/bootstrap/settings.
5. PostgreSQL schema, security/ACL/RLS, types/round-trips, and guarded support.
6. PostgreSQL transaction diagnostics, rollback/atomic registration, and hardening.

Slice 1 is measured from `5730050`; every later slice is measured from its immediate accepted parent. Never use the cumulative original-`main` diff for the 399-line gate.

## Production-Fix Policy

If a fresh test proves a real defect against an authority, record minimal evidence and permit only the minimal fix in that slice. If code plus evidence threatens 399 lines, stop and re-slice before editing or continuing. No opportunistic refactor or behavior expansion; broader behavior requires an explicit decision.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `backend/tests/` | New | Fresh unit/contract suite |
| `backend/integration_tests/` | Modified | Contract-derived PostgreSQL proof |
| `supabase/migrations/20260722130455_create_raw_material_reception_storage.sql` | Referenced | Physical contract only |

## Risks and Rollback

| Risk | Mitigation |
|---|---|
| Misstated/fragile contract | Source hierarchy; deterministic, boundary-level assertions |
| Unsafe integration target | Fail-fast loopback guard; no `DATABASE_URL` fallback |
| Review overload | Baseline excluded; immediate-parent <=399-line slices |

Rollback each slice by reverting only its test/support files and any evidence-backed minimal fix; retain prior green slices. No schema rollback is planned.

## Acceptance Criteria and Success Metrics

- [ ] Every test derives from current authority and uses no prohibited technical input.
- [ ] All six slices are independently green within budget.
- [ ] PostgreSQL proofs cover security, constraints, transactions, and registration using the guarded local target.
- [ ] Unit/ASGI tests are deterministic, isolated, credential-free, and require no network or live database.
