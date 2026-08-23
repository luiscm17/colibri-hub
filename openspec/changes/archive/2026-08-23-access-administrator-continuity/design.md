# Design: Access Administrator Continuity

## Technical Approach

Access remains owner of the continuity policy and reserved-role semantics; Authentication remains owner of account lifecycle and provider operations. Add an Access-owned continuity port whose PostgreSQL adapter locks one singleton coordination row, joins `authentication_accounts`, `access_users`, current assignments, and the reserved role by `identity_subject`, and counts distinct principals in `active/active/current` state. Every ordinary reducing mutation acquires that lock, evaluates the post-mutation floor of two, and performs local database changes in the same SQLAlchemy transaction. Recovery remains a manual runbook with no route, use case, or provider bypass.

## Architecture Decisions

| Option | Tradeoff | Decision |
|---|---|---|
| Lock candidate assignment rows | No row exists for initialization; disjoint concurrent removals can lock disjoint rows | Reject |
| PostgreSQL advisory lock | Effective but implicit and harder to inspect operationally | Reject |
| Singleton continuity row plus `SELECT FOR UPDATE` | Visible migration state and one serialization point; negligible admin-write contention | Choose |
| Copy Auth status into Access | Faster query but stale cross-context authority | Reject; join authoritative tables through an adapter |
| Emergency backend endpoint | Automates recovery but creates a high-risk bypass | Reject; manual external governance only |

## Data Flow and Transactions

```text
HTTP use case (Auth or Access) -> shared SQLAlchemy Session
  -> lock access_administrator_continuity(id=1)
  -> query distinct operational principals across Auth + Access
  -> reject and rollback, or mutate local rows + append audit -> commit
  -> Auth only: provider ban/password/session work after durable local denial
```

The lock, decision, Access/Auth row updates, and database audits share one transaction. Provider calls remain outside that transaction; failures leave the account safely denied and use existing retry/operational handling. Account deletion remains outside this policy.

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/src/access/ports/administrator_continuity.py` | Create | Policy-facing lock/evaluate contract and enforcement state. |
| `backend/src/access/adapters/persistence/administrator_continuity.py` | Create | PostgreSQL join, distinct count, singleton lock. |
| `backend/src/access/application/deactivate_access_user.py` | Modify | Enforce floor two inside its atomic boundary. |
| `backend/src/access/application/replace_user_roles.py` | Modify | Enforce floor two before assignment revocation. |
| `backend/src/access/adapters/access_provisioning.py` | Modify | Expose atomic continuity assertion to Auth, not a stale boolean precheck. |
| `backend/src/auth/ports/access_provisioning.py` | Modify | Replace last-admin query with continuity assertion contract. |
| `backend/src/auth/application/{disable_account,reset_password}.py` | Modify | Assert continuity before local lifecycle mutation and commit. |
| `backend/src/bootstrap/{access_admin_dependency,auth_dependency}.py` | Modify | Inject one session-backed continuity adapter. |
| `backend/src/access/domain/errors.py`, `backend/src/auth/domain/errors.py` | Modify | Rename semantics/message to two operational administrators; preserve HTTP 409 mapping. |
| `supabase/migrations/<generated_timestamp>_enforce_administrator_continuity.sql` | Create | Singleton table (`id=1`, `enforcement_enabled`), indexes, RLS, revoked browser/service-role privileges. |
| `backend/integration_tests/test_access_control_critical.py` | Modify | Replace canonical-admin mutation with owned fixtures and concurrency evidence. |
| `backend/integration_tests/test_auth_lifecycle_local_supabase.py` | Modify | Cross-context floor and rollback/provider-order evidence with isolated fixtures. |
| `backend/tests/access/`, `backend/tests/auth/` | Modify | Floor-two and contract unit tests. |
| `docs/prd/access-control.md`, `docs/prd/auth.md`, `docs/data-models/conceptual/access-dictionary.md` | Modify | Define operational state, floor two, and ownership. |
| `docs/runbooks/administrator-recovery.md` | Create | Custody, approvals, emergency exception, evidence, closure, revocation, review. |

## Interfaces / Contracts

`assert_reduction_allowed(subject: str) -> None` locks continuity state and raises `AdministratorContinuityRequired` when enabled and the projected distinct operational count is below two. `enforcement_enabled` is changed only by reviewed migration/operations SQL; it is not exposed through FastAPI.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Operational predicate, distinct count, floor-two rejection, unchanged state | `unittest` fakes for all reducing use cases and error mapping. |
| Integration | Three-to-two success; two-to-one rejection; concurrent disjoint reductions; Auth/Access rollback; migration gate | Local PostgreSQL with per-test Auth accounts, Access users, assignments, and cleanup; assert canonical seeded admins unchanged. |
| API | No emergency/recovery operation | Inspect FastAPI OpenAPI paths and assert recovery requests are 404. No E2E infrastructure exists. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary is added; the design explicitly adds no recovery route.

## Migration / Rollout

Migration creates the singleton disabled, supporting indexes on Auth status/subject and current Access assignments, and restricted RLS-protected storage. Preflight SQL reports operational principals. Installations with one administrator must use controlled initialization or the external runbook to establish and evidence a second distinct active account/profile/current assignment. A guarded SQL step enables enforcement only when the locked count is at least two; otherwise it raises and changes nothing. Deploy application code after schema, enable per installation, retain transition evidence, and rollback code/schema together while retaining audits and recovery records.

## Open Questions

None.
