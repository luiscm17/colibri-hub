# Proposal: Access Module Hexagonal/DDD Audit

## Intent

Eliminate 6 categories of hexagonal architecture violations across the `access` module and shared infrastructure: anemic domain models, imprecise port contracts, `# type: ignore` suppressions, dependency direction violations, anti-patterns, and misplaced shared types. Delivers via inside-out chained PRs under 200 lines each.

## Scope

### In Scope
- Enrich domain entities with behavior methods and invariant guards
- Relocate `AuthenticatedIdentity` to a shared module
- Create dedicated `AssignmentRepository` port and adapter
- Eliminate all `# type: ignore` in `backend/src/`
- Fix adapter-to-application dependency direction violations
- Type the bootstrap composition (replace untyped dict provider)
- Clean namespace/file naming (no technology names)

### Out of Scope
- New features or capabilities
- Database schema changes
- Frontend changes
- Changes to test framework or test infrastructure
- Performance optimization

## Capabilities

### New Capabilities
None — pure refactor.

### Modified Capabilities
None — no spec-level behavior changes.

## Approach

Inside-Out with Chained PRs (4 PRs):

1. **PR1 — Domain Enrichment**: `user.deactivate()`, `role.grant_permission(p)`, `assignment.revoke(by, reason)`. Remove `Optional` where state is guaranteed post-creation.
2. **PR2 — Port Precision & Shared Types**: Type `list_recent` return, relocate `AuthenticatedIdentity` to `backend/src/shared/identity.py`, split `AssignmentRepository` from `RoleRepository`.
3. **PR3 — Adapter & Type Safety**: Fix all 5 `# type: ignore` (Supabase narrowing, pydantic-settings factory, SQLAlchemy result typing). Fix adapter→application DTO import.
4. **PR4 — Bootstrap & Namespace**: Typed use-case provider protocol, clean file naming.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/src/access/domain/users.py` | Modified | Add behavior methods, tighten types |
| `backend/src/access/domain/roles.py` | Modified | Add behavior, extract Assignment |
| `backend/src/access/domain/scopes.py` | Modified | Add behavior methods |
| `backend/src/access/ports/repositories.py` | Modified | Type returns, split AssignmentRepository |
| `backend/src/access/adapters/persistence/repositories.py` | Modified | Fix DTO import direction |
| `backend/src/access/adapters/http/router.py` | Modified | Remove cross-context import |
| `backend/src/warehouse/bales/ports/authorization.py` | Modified | Remove AuthenticatedIdentity |
| `backend/src/shared/identity.py` | New | AuthenticatedIdentity home |
| `backend/src/auth/adapters/identity_provider/admin_client.py` | Modified | Eliminate type: ignore |
| `backend/src/infra/configuration/application_settings.py` | Modified | Factory pattern for settings |
| `backend/src/warehouse/bales/adapters/persistence/bale_repository.py` | Modified | Fix type: ignore |
| `backend/src/bootstrap/access_admin_dependency.py` | Modified | Typed provider protocol |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Test breakage from entity API changes | Medium | Preserve dataclass construction; update test factories in same PR |
| Circular imports from domain enrichment | Low | Use domain `__init__.py` public API; no cross-layer imports |
| AssignmentRepository split ripples | Medium | PR2 updates all consumers atomically |
| Pydantic-settings workaround fragility | Low | Factory classmethod is documented pattern |

## Rollback Plan

Each PR is independently revertable. If a PR breaks CI, revert it without affecting others. The chained-PR strategy means earlier slices remain stable.

## Dependencies

- None external. Each PR depends only on its predecessor in the chain.

## Success Criteria

- [ ] Zero `# type: ignore` in `backend/src/`
- [ ] Zero Pyright errors
- [ ] Domain entities enforce invariants via behavior methods
- [ ] No cross-context imports (Access ↔ Warehouse)
- [ ] All 158 unit + 31 integration tests pass
- [ ] Structure follows capability-first hexagonal layout
