---
document_type: technical-spec
status: draft
implementation: not-applicable
scope: frontend/accessibility
authority: explanatory
owner: frontend
last_reviewed: 2026-08-11
---

# Frontend Accessibility Guidelines

This document defines transversal accessibility requirements for the Colibri Hub
frontend. Target conformance is **WCAG 2.1 Level AA**. Feature specifications add
only capability-specific semantics and outcomes.

---

## 1. Operability And Focus

All interactive elements must be operable via keyboard alone.

- Every focusable element has a visible focus indicator.
- Focus order follows the reading and task sequence without positive tab-order
  overrides.
- Composite widgets follow the established keyboard interaction for their
  exposed semantics.
- Overlays contain focus while active when required and restore it to a logical
  origin or successor when closed.
- Focus moves intentionally after navigation, validation failure, destructive
  change, and asynchronous completion; it is not reset without user benefit.
- Repeated navigation can be bypassed where it would otherwise obstruct access
  to primary content.

---

## 2. Perception And Visual Presentation

- Text meets a minimum contrast ratio of **4.5:1**, or **3:1** for large text.
- Meaningful graphical objects, focus indicators, and interactive boundaries meet
  **3:1** against adjacent colors where WCAG requires it.
- Color is never the only means of communicating status, selection, validation,
  or required action.
- Content remains understandable under supported zoom, text resizing, reflow,
  and color-scheme conditions.
- Essential information is available without relying on animation, and reduced
  motion preferences are respected.

The [Visual Identity](design-system/visual-identity.md) owns semantic token
definitions. Every applied combination still requires contrast and perception
validation; a component library or token name does not guarantee compliance.

---

## 3. Semantics, Names, And Feedback

- Prefer native semantics. Custom interactions expose an equivalent role, name,
  value, state, and relationship when native elements cannot express the need.
- Every control has an accessible name that describes its purpose; visible labels
  and accessible names remain consistent.
- Instructions, descriptions, and validation errors are programmatically
  associated with the control or region they explain.
- Headings, landmarks, lists, tables, and other structures preserve meaningful
  reading and navigation relationships.
- Loading, completion, validation, and error updates are announced with urgency
  appropriate to their effect without producing repetitive noise.
- Feedback is concise, actionable, and available through more than visual
  placement alone.

---

## 4. Content And Navigation

- Page titles and the announced page context identify the active view after
  navigation.
- Heading levels and landmarks describe the content hierarchy consistently.
- Informative non-text content has an equivalent text alternative; decorative
  content is ignored by assistive technology.
- Link and control purpose is understandable from its accessible name and
  relevant context.
- Language, terminology, instructions, and errors are clear and consistent.

---

## 5. Validation Responsibilities

Feature teams validate applicable requirements through a combination of:

- automated checks for deterministic structural failures;
- keyboard-only interaction and focus review;
- screen-reader validation of names, states, relationships, and announcements;
- visual review of contrast, zoom, reflow, color independence, and motion; and
- scenario review for error recovery and task completion.

The [Testing Strategy](testing/strategy.md) owns validation levels and automation
boundaries. The [Editable Batch Grid](patterns/editable-batch-grid.md) owns the
additional observable contract for that interaction pattern.
