# PRD Template

> Copy this template when creating a new Product Requirements Document.
> Fill in the YAML frontmatter below and replace placeholder text with actual content.
> Remove this instruction block before finalizing.

```yaml
---
document_type: prd
status: draft
implementation: not-started
scope: <context/capability, e.g. "warehouse/bales">
authority: normative
owner: product
last_reviewed: <YYYY-MM-DD>
replaces: null
---
```

## Business Scope

<!-- Brief introduction: what business area or capability this PRD covers, why it exists, and what value it delivers. -->

## Problem Statement

<!-- What problem are we solving? What is the current situation and why is it inadequate? -->

## Stakeholders and Actors

| Actor | Role | Interaction |
|-------|------|-------------|
| <!-- Actor name --> | <!-- Role description --> | <!-- How they interact with this capability --> |

## Business Rules

<!-- Numbered list of business rules that govern this capability. These are the authoritative source — technical specifications reference these rules, never redefine them. -->

1. <!-- Rule -->
2. <!-- Rule -->

## Flows and Processes

<!-- Describe the main business flows. Use numbered steps, sequence descriptions, or diagrams as appropriate. -->

### Primary Flow

1. <!-- Step -->
2. <!-- Step -->

### Alternative Flows

<!-- Document alternative paths, exceptions, and error conditions. -->

## States and Transitions

<!-- If the capability involves stateful entities, document valid states and allowed transitions. Remove this section if not applicable. -->

| State | Description | Allowed Transitions |
|-------|-------------|---------------------|
| <!-- State --> | <!-- Description --> | <!-- Target states --> |

## Acceptance Criteria

<!-- Verifiable conditions that define when this capability is correctly implemented. Use Given/When/Then or declarative style. -->

1. <!-- Criterion -->
2. <!-- Criterion -->

## Open Items and Pending Decisions

<!-- Business decisions that remain unresolved. Each item should identify what needs to be decided, who owns the decision, and what the impact of deferral is. -->

| Item | Owner | Impact | Status |
|------|-------|--------|--------|
| <!-- Decision needed --> | <!-- Who decides --> | <!-- What is blocked --> | <!-- open/resolved --> |
