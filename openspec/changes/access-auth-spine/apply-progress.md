# Apply Progress: Access Authorization Spine

**Work unit:** `pr1-access-domain-application`  
**Delivery:** feature-branch-chain; PR #1 child targets `back/access-auth-spine`  
**Mode:** Standard (`strict_tdd: false`)

## Status

Completed assigned PR #1 core tasks 1.1–1.3. Phase 2 persistence/migration and
Phase 3 HTTP/Warehouse work remain intentionally unimplemented.

## Prior Progress Preserved

| Prior required surface | Estimated additions + deletions |
|---|---:|
| Domain models and policy rules (task 1.1) | 150 |
| Application ports, use cases, audit, and mutation invariant (task 1.2) | 260 |
| SQLAlchemy records, mappings, repositories, registry, package discovery (task 1.4) | 300 |
| Imperative migration with constraints, RLS/ACL, indexes, and safeguards (task 1.3) | 250 |
| Unit and PostgreSQL concurrency/atomicity proof required by tasks 1.1–1.3 | 380 |
| **Prior total forecast before revised three-PR plan** | **1,340** |

## Task State

- [x] 1.1 Access domain models and policy tests
- [x] 1.2 Application behavior, bootstrap, mutations, and audit tests
- [x] 1.3 Mutation authorization, audit contract, and serialized invariant tests
- [ ] 2.1 SQLAlchemy persistence and registry
- [ ] 2.2 Migration safeguards
- [ ] 2.3 PostgreSQL proof
- [ ] 3.1–3.4 HTTP, composition, and Warehouse integration
- [ ] 4.1 Final chain verification

## Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `uv run --locked --package backend python -m unittest backend.tests.test_access_spine -v` — exit 0, 7 tests passed. |
| Full unit suite | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0, 39 tests passed. |
| Runtime harness command/scenario and exact result | N/A: this PR has no runtime boundary; it is framework-free domain/application code proven through deterministic store doubles. |
| Rollback boundary | Remove `backend/src/access/` and `backend/tests/test_access_spine.py`; no existing application, persistence, HTTP, or Warehouse behavior changes. |

## Delivery and Diff Evidence

- Delivery: `auto-chain`, `feature-branch-chain`; PR #1 targets tracker `back/access-auth-spine` from `back/access-auth-spine-core`.
- Changed core/test lines: 354 additions, 0 deletions before planning-artifact checkbox/progress updates; below the user-approved 800-line ceiling.
- `git diff --check -- backend/src/access backend/tests/test_access_spine.py openspec/changes/access-auth-spine` — exit 0.
