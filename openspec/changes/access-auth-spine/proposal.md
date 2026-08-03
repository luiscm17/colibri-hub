# Proposal: Access Authorization Spine

## Intent

Establish the first deployable Access authorization foundation without implementing Authentication. It replaces the current unprotected Warehouse write with server-side, persisted, default-deny authorization while preserving the separation: Authentication establishes identity; Access decides permissions.

## Scope

### In Scope
- Persisted Access profiles, additive roles, exact action-and-scope permissions, active-state evaluation, reserved System Administrator semantics, and two registered scopes: `access_control` and `warehouse.raw_materials`.
- Controlled, idempotent bootstrap from an externally supplied opaque provider subject; it creates the initial active System Administrator and redacted initialization audit.
- Minimal profile/role/assignment mutation commands that enforce the last-operational-System-Administrator invariant end-to-end.
- `GET /api/v1/access/me`; generic `403 access_denied` for the protected resource and specific missing/inactive-profile results for self access.
- Fail-closed production HTTP (`401`) until Authentication supplies a validated identity; deterministic injected identity seams for tests.
- Protect only `POST /api/v1/warehouse/bales` with `write + warehouse.raw_materials`, before business mutation.
- Forward-only migration, RLS/ACL defense in depth, and unit, HTTP/composition, and PostgreSQL integration evidence.

### Out of Scope
- Authentication providers, Supabase Auth configuration/SDKs, token or session validation, credentials, and frontend work.
- Presets, broad Access administration, scope catalog expansion, other protected operations, caching, direct grants, denies, wildcard/hierarchical scopes, and job/shift authorization.

## Capabilities

### New Capabilities
- `access-authorization-spine`: persisted Access policy, bootstrap, self-access, invariant-enforcing mutations, and audit behavior.
- `warehouse-bale-registration-authorization`: server-derived authorization requirement for batch registration.

### Modified Capabilities
None; `openspec/specs/` has no existing capabilities. The broader backend Access specification remains the roadmap, not this slice's contract.

## Approach

Add an Access bounded context behind ports and inject a narrow authorization port into Warehouse. Access stores opaque subjects only; production composition denies unvalidated requests. Use one imperative migration without freezing table-level design here.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `backend/src/access/` | New | Access domain, application, ports, adapters |
| `backend/src/bootstrap/`, `backend/src/warehouse/bales/` | Modified | Composition, route protection, CORS |
| `backend/pyproject.toml`, `infra/persistence/record_registry.py` | Modified | Package and ORM registration |
| `supabase/migrations/` | New | Access persistence and database safeguards |
| `backend/tests/`, `backend/integration_tests/` | Modified | Authorization and PostgreSQL proof |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Local schema drift invalidates integration evidence | High | Reset with `pnpm supabase db reset --local --no-seed`; change schema only via migrations |
| Pre-Authentication route is unusable | Certain | Intentional fail-closed `401`; later Authentication composes validation |
| Work exceeds 800 review lines | Medium | Plan two coherent slices before apply; do not choose chain strategy yet |

## Rollback Plan

Deploy a forward-only compensating migration and remove the dependent composition/package changes as one release unit; restore the prior unprotected registration route only through an explicitly approved rollback.

## Dependencies

- User-run dependency installation only, if later required.
- Local PostgreSQL reset before verification; no out-of-migration repair.
- A later Authentication adapter to validate provider tokens or sessions.

## Success Criteria

- [ ] Denied/missing/inactive identities cannot mutate Warehouse; allowed exact permissions can.
- [ ] Bootstrap and all included invariant-affecting mutations preserve one operational System Administrator.
- [ ] Unit and PostgreSQL tests prove policy, migration, bootstrap, audit, and denial-before-mutation behavior.
- [ ] Candidate delivery boundaries are persisted Access core/migration versus Warehouse HTTP composition/proof, pending explicit chain-strategy selection.
