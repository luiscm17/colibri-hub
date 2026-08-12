```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:69aee73be7a4ecb7a3692c5d6063a43247ac42c86512d304c00c31c73f49d4d8
verdict: fail
blockers: 7
critical_findings: 7
requirements: 0/7
scenarios: 0/7
test_command: pnpm vitest run --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism
test_exit_code: 0
test_output_hash: sha256:f3a6240a52ea8091781ed5bfca5fd68b22e8d5bd5c329fbbe9b95ddabbd1a47a
build_command: pnpm build && pnpm lint
build_exit_code: 0
build_output_hash: sha256:a14e1679eb410991298fa84e10412def1424a1f7f71e303180db98b761e8255a
```

## Verification Report

**Change**: frontend-access-control
**Version**: N/A
**Mode**: Standard

### Completeness
| Metric | Value |
|---|---:|
| Tasks total | 30 |
| Tasks complete | 30 |
| Tasks incomplete | 0 |

### Build & Tests Execution
**Build**: Passed — `pnpm build && pnpm lint` exited 0. TypeScript, Vite production build, and ESLint passed. Vite emitted its existing chunk-size warning for a 660.18 kB minified asset.

**Tests**: Passed — `pnpm vitest run --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism` exited 0. The exact stdout/stderr digest is recorded in the YAML envelope.

**Coverage**: Not available; no coverage command or threshold is configured.

### Spec Compliance Matrix
| Requirement | Scenario | Test/runtime evidence | Result |
|---|---|---|---|
| Access State and Handoff | Handoff | `access-controller.test.ts` and `AccessProvider.test.tsx` pass, but do not exercise every handoff through protected content or prove Authentication's opaque handoff contract. | PARTIAL |
| Access State and Handoff | Stale bootstrap | `access-controller.test.ts` passes for a controller race; no provider/integration publication test covers the full scenario. | PARTIAL |
| Fail-Closed Decisions | Decision | `access-controller.test.ts` passes exact/compound and malformed cases, but does not cover a complete declared matrix. | PARTIAL |
| Protected Capability Boundaries | Revocation | `httpClient.test.ts` passes one-refresh/no-replay; recorded maintainer evidence exists, but no passing automated scenario covers direct/history plus visible action and safe-input behavior together. | PARTIAL |
| Addressable Administration | Recovery | `AdministrationPage.test.tsx` passes latest-page, missing-user, filters, and abort cases; it does not cover dirty discard/origin restore, all families, stale denied fallback, or invalid/empty-page reconciliation. | PARTIAL |
| Governance and History | Governance | `governance.test.ts` passes mutation-gate classification only; UI/API behavior for independent presets, recognized scopes, lifecycle, and traceability is not covered. | PARTIAL |
| Mutation and Concurrency | Conflict | `governance.test.ts` passes classification only; it does not exercise a previewed role/assignment edit or 409 with fresh preview in the UI. | PARTIAL |
| Accessible, Safe, and Evidenced Delivery | Evidence | Passing deterministic tests and recorded maintainer observations exist, but no automated test covers the complete accessibility, deferred-code, draft-clearing, and responsive scenario. | PARTIAL |

**Compliance summary**: 0/7 scenarios compliant. Each scenario has partial evidence, but none has a complete passing covering test as required by the verification contract.

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|---|---|---|
| Access State and Handoff | PARTIAL | Controller implements five states, strict adaptation, correlation, abort, and clearing. Authentication opaque handoff identity remains externally asserted rather than independently proven. |
| Fail-Closed Decisions | PARTIAL | Adapter uses exact action/scope checks and rejects malformed variants. |
| Protected Capability Boundaries | PARTIAL | Catalog and route guard are exact; shared HTTP recovery prevents replay. Full visible-action consistency is not demonstrated. |
| Addressable Administration | NOT IMPLEMENTED | The rendered administration surface lacks create/edit entry flows without a mounted row, dirty Back/Cancel confirmation and origin restoration, and complete family recovery. |
| Governance and History | NOT IMPLEMENTED | No scope governance form is rendered; role/preset creation, preset copy flows, recognized-scope lifecycle, and matrices are not implemented by the visible administration surface. |
| Mutation and Concurrency | PARTIAL | MutationGate tracks fingerprints and recovery classes, but the rendered UI does not implement a fresh preview/confirmation workflow. |
| Accessible, Safe, and Evidenced Delivery | PARTIAL | Latest-only requests and abort silence are present; complete selector announcement, focus-return, draft/security, and responsive guarantees lack complete runtime coverage. |

### Coherence (Design)
| Decision | Followed? | Notes |
|---|---|---|
| Separate Access capability with narrow public contract | Yes | `features/access-control` owns controller, provider, catalog, and administration surface. |
| Exact catalog plus identity; backend authority | Yes | Access checks compare exact action/scope values and strict `authorization.is_global`; route catalog is explicit. |
| Backend governance with previews, versions, and reasons | No | `GovernancePanel` submits lifecycle/replacement directly and exposes no preview/confirmation flow; several planned governance surfaces are absent. |
| Addressable independent administration families | No | `AdministrationPage` has collection/detail navigation but no create/edit entry flows without a mounted row and incomplete family operations. |

### Issues Found
**CRITICAL**:
1. No specification scenario has a complete passing covering test; 0/7 scenarios are compliant under the SDD runtime-evidence rule.
2. The administration implementation does not satisfy the required addressable create/edit, dirty-discard/origin restoration, and complete recovery behavior.
3. Governance lacks rendered scope lifecycle/recognition, role and preset creation/copy flows, and required independent-role behavior.
4. The required fresh preview/confirmation workflow for role and assignment replacement is absent from the rendered mutation path.
5. The visible action hide/disable consistency and full revocation scenario are not covered by a passing runtime test.
6. The complete accessibility/evidence scenario lacks a passing covering test for announcements, semantic focus return, deferred unauthorized code, responsive parity, and draft-clearing disclosure controls.
7. Authentication's opaque handoff identity/session-ended contract is recorded as external evidence but is not independently covered by this change's runtime test suite.

**WARNING**:
- Vite reports an existing production chunk above 500 kB; build remains successful.
- CodeGraph was unavailable because the repository has no `.codegraph` index; source inspection used direct file reads after that documented fallback.

**SUGGESTION**:
- Add scenario-level integration and interaction tests before requesting another final verification attempt.

### Verdict
FAIL
The test, build, and lint commands passed, but this is a product verification failure: required administration/governance behavior is missing and no specification scenario has complete passing runtime test coverage. This is not a Gentle AI, provider, or tooling failure.
