---
document_type: technical-spec
status: draft
scope: frontend/testing
authority: explanatory
owner: frontend
---

# Frontend Testing Strategy

This strategy defines durable frontend test levels, responsibilities, and
completion criteria. Dependency manifests, scripts, and repository configuration
record which tools and executable quality gates are available.

---

## 1. Principles

- Test observable behavior and contracts, not internal component structure.
- Put each risk at the lowest test level that proves it with sufficient
  confidence; use broader levels for integration and workflow risks.
- Keep backend policy authoritative. Frontend tests prove presentation,
  adaptation, and interaction behavior rather than reimplementing domain rules.
- Treat deterministic automation and human evaluation as complementary.
- A feature is not adequately covered merely because it builds or renders.

## 2. Test Levels

| Level | Responsibility | Typical risks |
| --- | --- | --- |
| Focused logic | Prove deterministic transformations and state decisions without rendering | Payload adaptation, validation presentation, state transitions, stale-result rejection |
| Interaction | Prove behavior through the same controls and feedback a user observes | Forms, keyboard behavior, focus, loading, denied states, recoverable errors |
| Integration | Prove boundaries cooperate using realistic contracts | Routing, authentication and authorization handoffs, transport adaptation, capability composition |
| Workflow | Prove a critical user outcome across the running application and its required services | High-value operational journeys, recovery, concurrency, and cross-screen continuity |

The implementation mechanism for a level may change without altering the risk
or responsibility assigned to that level.

## 3. Feature Scenarios

Feature specifications own capability-specific scenarios and acceptance
outcomes. For each scenario, the implementation identifies:

- the behavior or risk being proved;
- the narrowest sufficient test level;
- required contract fixtures or service boundaries;
- accessibility and recovery observations; and
- any part that requires manual validation.

Shared patterns define reusable observable contracts. Features adopting a
pattern must test their feature-specific configuration and the portions of that
contract that carry material risk; they do not need to duplicate the pattern
document in every feature specification.

## 4. Automation And Manual Validation

Automate behavior that is deterministic, repeatable, and valuable as a
regression signal. Manual validation remains required where meaningful evidence
depends on assistive technology, visual perception, motion, device behavior, or
exploratory judgment.

The [Accessibility Guidelines](../accessibility.md) define accessibility
requirements and validation responsibilities. Automated checks may identify
common violations, but they do not establish conformance by themselves.

## 5. Completion Criteria

Frontend work is test-complete when:

- required feature scenarios are covered at justified levels;
- important success, failure, denied, empty, loading, and recovery outcomes are
  exercised where applicable;
- keyboard, focus, input preservation, and accessible feedback are validated for
  interactions that depend on them;
- contract boundaries are tested without coupling assertions to implementation
  structure; and
- required manual checks are recorded and performed rather than silently
  replaced by automation.

## 6. Access Control Evidence Boundary

Access Control uses focused Vitest coverage for state adaptation, exact
authorization decisions, stale-result rejection, route outcomes, and recoverable
client feedback. The standard deterministic gate is `pnpm vitest run
--reporter=verbose`, followed by `pnpm build` and `pnpm lint` from `frontend/`.

Real-session and assistive-technology evidence remains a separate manual level:
the maintainer must start the existing services and record Authentication handoff
and session clearing, protected `403` recovery, pagination and mutation recovery,
narrow-viewport critical actions, keyboard/focus behavior, and announcements.
Automation does not replace that evidence or make the frontend authoritative for
authorization. For the current Access Control slice, maintainer evidence recorded
handoff/session clearing, latest-only navigation, responsive critical actions,
keyboard/focus, announcements, and no replay as passed. The only frontend gap was
an invalid inline reduced-motion media key; it was moved to the existing valid
global CSS media query without changing authorization or Authentication behavior.
