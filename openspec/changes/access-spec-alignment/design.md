# Design: Access Spec Alignment

## Overview

Close the missing ~60% of the `access` admin API surface (spec §9–§10) and fix contract divergences, delivered as a 5-PR feature-branch chain. Application-layer only: no schema/migration changes. Aligns namespace and router conventions with the `auth` module and moves the privileged-action invariant into the domain.

## Technical Approach

Close the `access` admin API gap (spec §9–§10) as a **feature-branch chain of 5 PRs**, each independently correct with green tests. Follow the established `auth` module conventions: `commands.py` + `results.py` (not `dto.py`), routers split by actor scope (`self_access_router.py` + `admin_router.py`), one file per use case. Privileged-action validation moves into the domain `Role` entity. Pagination is page-based. No migrations — the schema (§11) already covers all non-preset tables.

Per `arch-hexagonal-ddd` v2: dependency direction stays inward; ports own contracts; the domain owns the privileged-action invariant (spec §6.5, §8.2).

## Architecture

Hexagonal, dependency inward (domain ← application ← ports ← adapters). The change adds application use cases and HTTP adapters, hardens one domain entity, and extends port contracts for pagination. No new bounded context, no cross-context coupling. Decisions below.

| Decision | Choice | Alternatives rejected | Rationale |
|----------|--------|----------------------|-----------|
| Pagination model | Page-based (`page`, `page_size`) + `PaginatedResponse[T]` envelope `{items,page,page_size,total}` | Cursor-based | Spec §10 permits either; page-based is simpler, testable with fixtures, no real DB yet. Repo list methods gain `limit`/`offset` + `count`. |
| Router split | Two factories in two files mirroring `auth` (`create_self_access_router`, `create_admin_router`) | Single router; router-per-resource | Auth convention is the reference; actor-scope split matches authz boundary (`_require_admin`). |
| Privileged-action check | Add `Role.set_permissions()` (full-replace) + move `PRIVILEGED_ACTIONS` rejection into `Role` | Keep check only in use cases | Spec §6.5/§8.2 assign this invariant to the domain; use cases delegate. |
| Dead code removal | Repoint every importer to specific port/adapter modules, THEN delete `repositories.py` shims | Delete shims immediately | Shims are NOT dead — 4+ modules import them. Deleting first breaks the build. |
| Container growth | Extend `AdminUseCases` dataclass + `admin_use_case_dependency` additively | New sub-containers | Keeps one typed container; existing bootstrap wiring stays intact. |

## Data Flow

    HTTP admin_router ──_require_admin(manage_access)──▶ UseCase.execute(Command)
          │                                                   │
          │                                          TransactionPort.atomic()
          ▼                                                   ▼
    PaginatedResponse[T]  ◀── Result ◀── domain (Role.set_permissions) + Audit.append

## PR Split (feature-branch-chain)

Tracker branch: `back/fix-59-access-spec-alignment`. PR1 targets the tracker; each later PR targets the previous PR branch. Only the tracker merges to `main`.

| # | Branch | Scope | Depends on |
|---|--------|-------|-----------|
| 1 | `back/fix-59-01-namespace-split` | Mechanical: `dto.py`→`commands.py`+`results.py`; `router.py`→`self_access_router.py`+`admin_router.py`; repoint all imports; delete dead re-export shims | — (tracker) |
| 2 | `back/fix-59-02-domain-and-me` | `Role.set_permissions()` + domain privileged-action check; `/access/me` adds `roles[]`, renames `global_access`→`global` | PR1 |
| 3 | `back/fix-59-03-role-scope-lifecycle` | Use cases `UpdateRole`, `ActivateRole`, `DeactivateRole`, `ActivateScope`, `DeactivateScope`; endpoints `GET /roles/{id}`, `PATCH /roles/{id}/status`, `PATCH /scopes/{id}/status`; container + bootstrap wiring | PR1, PR2 |
| 4 | `back/fix-59-04-user-detail-status` | `GetAccessUser` use case; endpoints `GET /users/{id}`, `PATCH /users/{id}/status`; wire activate/deactivate user | PR1 |
| 5 | `back/fix-59-05-pagination-audit` | `PaginatedResponse[T]`; `page`/`page_size` on all list endpoints; port `limit`/`offset`+`count`; audit filters (`subject_type`, `change_kind`, date range) | PR3, PR4 |

## File Changes

| File | PR | Action | Description |
|------|----|--------|-------------|
| `access/application/commands.py` | 1 | Create | All command dataclasses moved from `dto.py` |
| `access/application/results.py` | 1 | Create | All result dataclasses + `PermissionInput` |
| `access/application/dto.py` | 1 | Delete | Superseded by commands/results |
| `access/adapters/http/self_access_router.py` | 1 | Create | `/access/me` factory |
| `access/adapters/http/admin_router.py` | 1 | Create | Admin endpoints factory |
| `access/adapters/http/router.py` | 1 | Delete | Split into the two above |
| `access/ports/repositories.py` | 1 | Delete | Dead shim (after repointing imports) |
| `access/adapters/persistence/repositories.py` | 1 | Delete | Dead shim (after repointing imports) |
| `access/application/*.py`, `containers.py` | 1 | Modify | Repoint imports to `commands`/`results` + specific ports/adapters |
| `bootstrap/api_router.py`, `bootstrap/access_admin_dependency.py` | 1,3,4 | Modify | New router names; wire new use cases |
| `access/domain/roles.py` | 2 | Modify | `set_permissions()` + privileged-action rejection |
| `access/application/results.py`, `get_current_access.py` | 2 | Modify | Add `roles[]` to result |
| `access/adapters/http/models.py`, `self_access_router.py` | 2,5 | Modify | `global` rename, `roles[]`, `PaginatedResponse` |
| `access/application/update_role.py`, `activate_role.py`, `deactivate_role.py`, `activate_scope.py`, `deactivate_scope.py`, `get_access_user.py` | 3,4 | Create | New use cases |
| `access/ports/roles.py`, `scopes.py`, `users.py`, `audit.py` | 5 | Modify | `limit`/`offset`/`count`; audit filters |
| `access/adapters/persistence/*_repository.py` | 5 | Modify | Implement pagination + filters |
| `backend/tests/**` | 1–5 | Modify | Unit + API tests per slice |

## Components and Interfaces

```python
# results.py — /access/me now carries roles
@dataclass(frozen=True, slots=True)
class RoleSummaryResult:
    role_id: str; code: str; name: str

# domain/roles.py — full-replace with domain invariant
def set_permissions(self, permissions: set[Permission]) -> None:
    if not self.is_system_administrator:
        if any(p.action in PRIVILEGED_ACTIONS for p in permissions):
            raise PrivilegedActionRequiresSystemAdministrator()
    self.permissions = set(permissions)
```

`/access/me` authorization block: `global` (was `global_access`), plus top-level `roles: [{role_id, code, name}]` (spec §10.1). Response models keep `strict=True, extra="forbid"`.

## Data Models

No schema changes — existing tables (spec §11: `access_users`, `access_roles`, `access_user_role_assignments`, `access_scopes`, `access_role_permissions`, `access_change_audits`) already back every non-preset endpoint. Changes are in-memory command/result dataclasses and Pydantic HTTP models only:

- `commands.py` / `results.py` — split from `dto.py`; add `RoleSummaryResult`.
- `models.py` — `PaginatedResponse[T]` generic envelope; `CurrentAccessResponse` gains `roles[]`; `AuthorizationResponse.global` replaces `global_access`.
- Repository adapters read the same tables with added `LIMIT`/`OFFSET` and `COUNT` for pagination.

## Correctness Properties

### Property 1: Ordinary roles reject privileged actions

`Role.set_permissions()` raises `PrivilegedActionRequiresSystemAdministrator` if a non-sys-admin role receives `manage_access` or `edit_outside_window`, regardless of caller.

**Validates: Requirements 6.5, 8.2**

### Property 2: Mutation-audit atomicity

Every admin mutation writes exactly one audit row and increments the affected `authorization_version`/`version` inside the same `TransactionPort.atomic()` block, gated by `expected_version`.

**Validates: Requirements 12.1, 15.1**

### Property 3: Full-replace determinism

After `set_permissions(P)`, the role's permission set equals the validated `P` (no partial merge, no residual pairs).

**Validates: Requirements 9.2**

### Property 4: Pagination is total-preserving

For any `page`/`page_size`, `total` equals the full result count and `len(items) <= page_size`.

**Validates: Requirements 10.1, 16.1**

### Property 5: Slice integrity

After each PR the full unit suite is green — no slice leaves the module uncompilable or with failing imports.

**Validates: Requirements 18.1, 18.2**

## Error Handling

Reuse existing domain exceptions mapped to the shared envelope (spec §14): `access_version_conflict` (409), `access_role_not_found`/`access_scope_not_found`/`access_user_not_found` (404), `privileged_action_requires_system_administrator` (422), `last_system_administrator_required` (409), `reserved_role_mutation_forbidden` (422). New status endpoints validate `expected_version` before mutation and raise on mismatch. Invalid pagination params (`page < 1`, `page_size` out of bounds) → 422 via Pydantic validation.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit (domain) | `Role.set_permissions` rejects privileged actions on ordinary roles; accepts on sys-admin | stdlib `unittest` |
| Unit (application) | Update/activate/deactivate role & scope: version conflict, not-found, audit written; `GetAccessUser` assignments+perms | fakes/in-memory repos |
| API | New endpoints reject ordinary user (403); `/access/me` global + ordinary shapes incl. `roles[]`; pagination params; strict extra-field rejection | FastAPI TestClient with injected session |
| Integration | Deferred — no schema change; existing PG tests still pass | `TEST_DATABASE_URL` suite unchanged |

Run per PR: `uv run --locked --package backend python -m unittest discover -s backend/tests -v`.

## Threat Matrix

N/A — no shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. Security requirement (design-level, spec §16): every new admin endpoint MUST route through the existing `_require_admin` dependency (`manage_access` in `access_control`); every mutation MUST enforce `expected_version` and write one audit row in the same `TransactionPort.atomic()` block.

## Migration / Rollout

No migration required — schema (§11) already supports all non-preset endpoints. Rollback = revert the PR branch; application-layer only.

## Open Questions

- [ ] `RoleSummaryResult` field names: spec §10.1 uses `code`/`name` (not `role_code`/`role_name`) inside `roles[]` — confirmed from spec example; keep spec names.
- [ ] Pagination default `page_size` (proposed 50) — confirm with API conventions doc if one exists.
