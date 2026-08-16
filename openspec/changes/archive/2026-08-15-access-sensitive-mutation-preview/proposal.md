# Proposal: Access Sensitive Mutation Preview

## Intent

Close #84 by making complete user-role replacement and shared-role permission replacement safe, reviewable operations. An administrator must see a fresh backend-derived impact and explicitly confirm before either sensitive PUT can run.

## Scope

### In Scope
- Require a fresh, matching preview and one explicit confirmation for user complete-role replacement and shared-role permission replacement.
- Integrate shared-role preview/confirmation into #83's canonical `RoleWorkflow`; retire the parallel shared-role mutation authority.
- Block only a full semantic no-op (unchanged permissions, name, and description); permit metadata-only role updates with a separate local diff, fresh preview, and confirmation. Collect an optional reason before preview; invalidate preview and confirmation after any relevant draft change, including reason-only edits.
- Present backend impact count first with accessible expandable identifiable-user evidence; show role metadata changes as a separate local diff.
- Define later delta-spec, technical-document, automated-contract, and real-backend/browser evidence work for these flows.

### Out of Scope
- #78 selection/membership, #85 reason-policy enforcement, #86 identifier validation, new endpoints, and broad #82/#83 rework.
- Backend authorization, preview calculation, and existing wire contracts.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `frontend-access-control`: tighten sensitive mutation preview/confirmation, invalidation, accessible impact, canonical ownership, and evidence requirements.

## Approach

Extend the Access administration capability—not routing or matrix ownership. Reuse existing preview endpoints and gate semantics, bind the preview to normalized impact-bearing draft, subject/version, authority, and request generation; additionally invalidate it when reason or local metadata changes. A metadata-only role update is previewed and confirmed as the complete role update, while its local diff stays distinct from backend permission impact. `RoleWorkflow` becomes the sole shared-role apply path. The UI remains advisory: backend authorization, version checks, invariants, and #85's optional/trimmed-reason policy stay authoritative. Later phases update the delta spec and the frontend Access technical spec; implementation tasks auto-chain if forecast above 400 changed lines.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `frontend/src/features/access-control/administration/roles/RoleWorkflow.tsx` | Modified | Canonical shared-role preview/confirm flow. |
| `frontend/src/features/access-control/administration/mutations/` | Modified/Removed | Reuse gates/impact UI; retire parallel authority. |
| `openspec/specs/frontend-access-control/spec.md` | Modified | Delta requirements and scenarios. |
| `frontend/docs/features/access-control.md` | Modified | Consumed-contract and evidence documentation. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Apply bypass or stale confirmation | Med | Gate every sensitive PUT; prove invalidation and single-submit behavior. |
| Divergent role ownership | Med | Migrate into `RoleWorkflow` and remove obsolete path. |
| Large impact obscures identities | Low | Count-first disclosure with accessible expansion. |

## Rollback Plan

Revert only the #84 frontend workflow, gate, test, and documentation work; backend endpoints/contracts remain unchanged. Restore the prior #83 `RoleWorkflow` behavior only if the preview integration causes regression, never retain two mutation authorities.

## Dependencies

- #83 supplies canonical `RoleWorkflow` and matrix ownership.
- #82 routing and dirty-departure behavior remains intact.
- #85 owns durable optional/trimmed-whitespace reason policy; #84 preserves compatible wire behavior.

## Success Criteria

- [ ] Neither sensitive PUT is emitted without a fresh matching backend preview and explicit confirmation; only a full semantic no-op cannot apply, while metadata-only role updates remain reviewable.
- [ ] Any relevant edit, including reason-only edits, conflict, denial, session/authority change, or failed apply invalidates confirmation.
- [ ] Shared-role mutation authority exists only through `RoleWorkflow`; metadata and impact are visibly distinct.
- [ ] Later verification records focused automated and code-level accessibility evidence for focus, status announcements, disclosure state, keyboard operation, non-color distinction, and responsive visibility. The sole manual closure scenario is a real shared-role revoked-authority `403`; real screen-reader execution is not a closure gate.
