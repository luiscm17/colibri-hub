---
document_type: runbook
status: active
implementation: not-applicable
scope: frontend
authority: normative
owner: architecture
last_reviewed: 2026-08-11
---

# Frontend Styling

Apply the [Visual Identity](../../frontend/docs/design-system/visual-identity.md)
through a Mantine-first styling policy. The
[Technology Baseline](../architecture/technology-baseline.md) owns the adopted
stack and version status; this document owns the durable styling decisions.

## 1. Application Order

Use the narrowest mechanism that preserves semantic tokens, theme modes, and
local ownership:

1. Select an existing semantic token or component default.
2. Use component properties for supported visual variations.
3. Use the component Styles API for state- or selector-specific adaptation.
4. Centralize a repeated, stable visual treatment through theme configuration or
   a reusable component boundary.
5. Use scoped CSS when the preceding mechanisms cannot express the requirement
   clearly.

This order is a decision guide, not a requirement to introduce custom component
factories or abstractions. Extraction is justified by stable reuse or ownership,
not by theoretical uniformity.

## 2. Token Application

- Apply semantic tokens by meaning rather than copying their literal values.
- Do not redefine brand, neutral, typography, spacing, radius, shadow, or motion
  scales outside Visual Identity.
- Prefer theme-aware values over hardcoded colors and dimensions when a semantic
  token exists.
- A feature may introduce a local value only when no shared semantic meaning
  exists. Repeated values are candidates for design-system review, not automatic
  global tokens.
- Mapping a business state to a semantic visual meaning belongs to the feature
  specification; defining the semantic token belongs to Visual Identity.

## 3. Scoped CSS

Scoped CSS is appropriate for styling that is clearer or only possible in CSS,
such as complex selectors, pseudo-elements, keyframes, or layout behavior that
the component API does not expose. Keep it with the responsibility that owns the
presentation and avoid selectors that depend on unrelated component internals.

File names, directories, and colocation choices may evolve with the source tree.
They are not architectural styling rules. Organization should preserve clear
ownership, deletion safety, and minimal coupling.

## 4. Reuse And Overrides

- Prefer local adaptation for a one-off presentation need.
- Consolidate repeated styling only when its semantics and change pressure are
  shared.
- Do not create global overrides for feature-specific presentation.
- Do not couple reusable styling to business-domain names or states.
- Avoid deep overrides of third-party internals when a supported extension point
  exists.

## 5. Accessibility Boundary

Styling must preserve visible focus, readable states, zoom and reflow behavior,
and reduced-motion preferences. The
[Accessibility Guidelines](../../frontend/docs/accessibility.md) own the exact
requirements and validation responsibilities; this policy does not duplicate
them or treat framework defaults as proof of compliance.
