# Technical Specification Template

> Copy this template when creating a new technical specification document.
> Fill in the YAML frontmatter below and replace placeholder sections with actual content.
> Remove sections marked "(if applicable)" that do not apply.

```yaml
---
document_type: technical-spec
status: <draft|active|superseded|archived>
implementation: <not-started|partial|implemented|not-applicable>
scope: <context/capability>
authority: explanatory
owner: <backend|frontend|platform>
last_reviewed: <YYYY-MM-DD>
replaces: <path|null>
---
```

## Overview

<!-- Purpose of this specification. What capability or component does it describe? -->

## Related PRD

<!-- Link to the normative PRD that defines the business rules this specification implements. -->

- PRD: [Capability Name](../prd/<area>/<capability>.md)

## Current State

<!-- Describe the current implementation status. What exists today? -->

## Target State

<!-- If the target differs from the current state, describe the approved end state here. Remove this section if current equals target. -->

## Technical Approach

<!-- Design decisions, architecture patterns, and implementation strategy. -->

## API Contract

<!-- (if applicable) Endpoints, request/response shapes, status codes, and versioning. -->

## Data Model

<!-- (if applicable) Tables, columns, constraints, relationships, and migration references. -->

## Error Handling

<!-- How errors are detected, classified, and communicated to callers or users. -->

## Testing Strategy

<!-- How this component is tested: unit, integration, property-based, or E2E. Include coverage expectations. -->

## Dependencies

<!-- Internal and external dependencies. Other services, libraries, or infrastructure this relies on. -->

## Open Items

<!-- Unresolved decisions, pending PRD clarifications, or known gaps to address. Remove when empty. -->
