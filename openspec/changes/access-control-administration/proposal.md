# Proposal: Access Control Administration

## Intent

Replace the minimal Access Spine (2-action evaluation engine, monolithic store, single endpoint) with the full administrative authorization layer required by the Access Control PRD and tech spec. The current spine cannot support frontend access-control screens, real provisioning coordination with Authentication, or business-scope management. This change delivers the CORE administrative surface (users, roles, assignments, scopes, audits) while deferring presets and impact previews.

## Scope

### In Scope

- Domain restructure: 5 actions (`read`, `write`, `edit`, `edit_outside_window`, `manage_access`), `AccessUser` entity with UUID/versions/timestamps, roles with name/description/`is_system_administrator` flag, assignments with revocation history, scope-definition catalog metadata
- Application layer: individual use cases per command/query — `CreateRole`, `UpdateRole`, `ActivateRole`, `DeactivateRole`, `ReplaceUserRoles`, `CreateAccessUser`, `ActivateAccessUser`, `DeactivateAccessUser`, `RegisterRecognizedScope`, `ActivateScope`, `DeactivateScope`, enhanced `GetCurrentAccess`, `ListAccessUsers`, `GetAccessUser`, `ListRoles`, `GetRole`, `ListScopes`, `ListScopeDefinitions`, `ListAccessAudits`
- Ports: per-aggregate repositories replacing monolithic `AccessStore`
- HTTP: ~15 admin endpoints (all require `manage_access`), enhanced `/access/me`
- Persistence: SQLAlchemy repositories + clean-break migration (drop spine tables, create spec-schema tables)
- Seed migration: 19 scope definitions from recognized catalog
- Auth integration: real `CreateAccessUser` adapter replacing `_FakeAccessProvisioning`
- Access-change audit with before/after JSONB snapshots
- Optimistic concurrency (`version` + `authorization_version`)
- Last-admin invariant (transactional)
- Tests: unit, API, integration (real local Supabase)

### Out of Scope

- Presets (`CreateRoleFromPreset`, CRUD presets, preset tables/endpoints)
- Impact previews (`PreviewRoleChange`, `PreviewUserRoleReplacement`)
- Warehouse endpoint protection (stock, detail, delivery authorization guards)
- Frontend Access Control UI
- Pagination/cursor on admin list endpoints (simple lists first)

## Capabilities

### New Capabilities

- `access-control-administration`: Full administrative layer — user lifecycle, role CRUD, scope registration, assignment management, audit queries, real provisioning coordination, optimistic concurrency

### Modified Capabilities

- `access-authorization-spine`: Domain restructured (5 actions, `AccessUser` entity, versioned aggregates), persistence pattern replaced (repository-per-aggregate), `/access/me` response enhanced with `authorization_version`

## Approach

**Clean-break migration** (confirmed): drop all spine tables, recreate with tech-spec schema. Pre-launch, no production data.

Implementation order:
1. Domain + ports (entities, value objects, repository protocols, domain errors)
2. Persistence + migration (SQLAlchemy repositories, clean-break SQL, scope-definition seed)
3. Application use cases (commands and queries, authorization_version increments)
4. HTTP + composition + auth wiring (admin endpoints, error translation, real provisioning adapter)

Architecture: hexagonal, package-by-capability, individual use-case classes (not monolithic service), repository-per-aggregate with `TransactionPort` for atomic boundaries.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/src/access/domain/` | Restructured | New entities, 5 actions, versioned aggregates, domain errors |
| `backend/src/access/application/` | Restructured | Replace monolithic `AccessApplication` with individual use cases |
| `backend/src/access/ports.py` | Replaced | Repository-per-aggregate ports, transaction port, clock/identity ports |
| `backend/src/access/adapters/persistence/` | Replaced | Individual repositories, new records matching spec schema |
| `backend/src/access/adapters/http_router.py` | Expanded | ~15 admin endpoints + enhanced `/access/me` |
| `backend/src/bootstrap/http_application.py` | Modified | Wire new repositories, replace `_FakeAccessProvisioning` |
| `supabase/migrations/` | New | Clean-break migration + scope-definition seed |
| `backend/tests/` | Rewritten | New unit + integration tests for restructured domain |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Auth integration contract mismatch | Medium | Read `ProvisionAccount` port contract before implementing adapter |
| Existing tests break immediately on migration | High | Rewrite tests in same PR batch that drops spine |
| Size (~1200-1500 lines) exceeds 400-line budget | High | Chained PRs: domain/ports → persistence → application → HTTP/wiring |
| `WarehouseAuthorizationAdapter` breaks on Action enum change | Low | Adapter already uses string-based matching; verify |

## Rollback Plan

Each chained PR is independently revertable via branch deletion from the tracker branch `back/access-control-administration`. If the full change needs reverting after merge to main: revert the migration (restore spine tables from previous migration), revert code PRs in reverse order. No production data exists to preserve.

## Dependencies

- Authentication module must expose its `AccessProvisioning` port contract (already exists as `_FakeAccessProvisioning` interface in bootstrap)
- Local Supabase for integration tests
- Tech spec §6-18 as implementation authority

## Success Criteria

- [ ] All 19 scope definitions seeded and queryable
- [ ] Admin can create roles, assign to users, and verify effective permissions via `/access/me`
- [ ] `_FakeAccessProvisioning` replaced with real adapter; `ProvisionAccount` creates access user
- [ ] Last-admin invariant enforced (cannot deactivate/unassign sole system administrator)
- [ ] Optimistic concurrency rejects stale writes with 409
- [ ] All access mutations produce audit entries with before/after snapshots
- [ ] Unit + integration tests pass on local Supabase
