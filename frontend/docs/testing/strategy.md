---
document_type: technical-spec
status: draft
implementation: not-started
scope: frontend/testing
authority: explanatory
owner: frontend
last_reviewed: 2026-07-27
---

# Frontend Testing Strategy

Testing approach and tooling decisions for the Colibri Hub frontend application.

---

## 1. Current State

No test runner or test framework is currently configured in the frontend workspace. There is no `test` script in `package.json`, no test configuration files, and no existing test files.

---

## 2. Target Stack

| Layer | Tool | Purpose |
| --- | --- | --- |
| Test Runner | Vitest | Fast, Vite-native test execution |
| Component Testing | @testing-library/react | DOM-based component interaction tests |
| Accessibility Checks | vitest-axe or jest-axe | Automated a11y rule validation per component |
| User Events | @testing-library/user-event | Realistic user interaction simulation |

---

## 3. Testing Layers

### 3.1 Unit Tests — Hooks and Logic

Test custom hooks, utility functions, form validation logic, and data transformations in isolation.

- Focus: pure logic, no DOM rendering
- Examples: form validators, data mappers, state derivation helpers

### 3.2 Component Tests — Interaction

Render components with Testing Library and verify behavior through user interactions.

- Focus: user-visible behavior, not implementation details
- Examples: form submission flows, grid row editing, navigation guards
- Each component test should include at least one accessibility assertion

### 3.3 Accessibility Tests — Automated Checks

Run axe-core rules against rendered components to catch common accessibility violations early.

- Focus: ARIA roles, color contrast (where detectable), keyboard operability
- Integrated into component tests rather than a separate suite

---

## 4. What Is Not Covered (Yet)

- **End-to-end tests**: No E2E framework (Playwright, Cypress) is planned for the current phase
- **Visual regression**: No screenshot comparison tooling configured
- **Performance testing**: No Lighthouse CI or bundle-size regression checks

These may be introduced in a future phase once the unit and component test foundation is stable.

---

## 5. Conventions

- Test files live alongside source files using the `.test.ts` or `.test.tsx` suffix
- Use `describe` blocks to group by feature or component behavior
- Prefer `getByRole` and `getByLabelText` queries over `getByTestId`
- Avoid mocking Mantine internals — test through the rendered DOM
- Keep test setup minimal; extract shared fixtures only when repeated across 3+ files
