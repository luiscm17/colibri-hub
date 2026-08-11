---
document_type: architecture
status: active
scope: frontend
authority: explanatory
owner: frontend
---

# Frontend Architecture Overview

This document defines the durable responsibilities, boundaries, and dependency
direction of the Colibri Hub frontend. It does not prescribe namespaces,
directories, filenames, component names, or feature-internal organization.

Product requirements remain authoritative for business behavior. Frontend
feature specifications describe presentation and interaction contracts. The
verified technology stack and cross-cutting implementation policies are owned by
the documents referenced in [Related Documents](#7-related-documents).

## 1. Responsibility Boundary

The frontend is a client of backend capabilities. It presents information,
collects user intent, and consumes backend decisions; it does not become a
second source of business truth.

The frontend owns:

- presentation state and interaction flow;
- local completeness and format feedback;
- adaptation of transport payloads into presentation models;
- preservation of safe user input across recoverable failures;
- capability-driven navigation and action availability;
- accessible loading, empty, denied, unavailable, and success states; and
- clear presentation of audit, concurrency, and correction consequences.

The backend remains authoritative for:

- identity and authorization decisions;
- business validation and state transitions;
- concurrency and consistency guarantees;
- effective permissions and business scopes;
- correction-window decisions; and
- persistence and audit history.

Client-side route guards, hidden actions, and local validation improve the user
experience but never replace backend enforcement.

## 2. Capability Ownership

Frontend responsibilities follow the business capabilities defined by the
product requirements and context map. A capability owns its presentation model,
interaction rules, and adaptation of the contracts it consumes.

| Capability | Frontend responsibility |
| --- | --- |
| Authentication | Present account entry, mandatory password replacement, session condition, and account administration without exposing credentials or provider internals |
| Access Control | Present effective authorization, protected navigation and actions, access profiles, roles, presets, scopes, assignments, and access history |
| Warehouse | Present Warehouse consultation and operational recording while preserving Warehouse business boundaries |
| Yarn Spinning | Present section and cross-section Yarn Spinning responsibilities without inferring authorization from organizational roles or shifts |
| Lot Processing | Present lot lifecycle and stage responsibilities while preserving stage-specific visibility and intervention boundaries |
| Shared Reference Data | Present reference information used across capabilities without becoming a shared business context |

Capability ownership does not require a particular source-tree layout. Code may
be reorganized as long as responsibilities remain cohesive and dependency
boundaries remain explicit.

## 3. Dependency Direction

Dependencies follow meaning and ownership rather than screen placement:

1. Presentation depends on the capability contracts it renders.
2. Capability-specific interaction logic depends on frontend models, not raw
   transport payloads.
3. Transport adaptation depends on backend API contracts but does not expose
   transport naming to presentation code.
4. Cross-cutting facilities support capabilities without owning their business
   rules.
5. Application composition coordinates capabilities without merging their
   ownership.

Frontend and backend specifications are independent technical projections of
the same product requirements. They integrate through explicit transport and
semantic contracts; neither specification dictates the other's namespaces,
modules, classes, providers, or component structure.

When one frontend capability depends on another, the dependency is expressed as
a semantic contract. For example, Access Control consumes the resolved
Authentication condition needed to decide whether authorization bootstrap may
begin. The contract does not require a particular state library, provider tree,
or component composition.

## 4. Contract Adaptation

Backend API contracts are consumed through an explicit frontend boundary that:

- attaches authentication material centrally where required;
- maps transport naming and envelopes into frontend models;
- validates required response variants rather than inventing defaults;
- normalizes known transport, validation, authorization, and availability
  failures into stable presentation outcomes;
- supports cancellation and prevents stale responses from replacing newer
  state; and
- never interprets a successful transport response as proof that a separate
  business rule was satisfied.

Feature specifications own the exact endpoints, payloads, mappings, and error
outcomes they consume. This overview owns only the boundary and dependency
principles.

## 5. State Ownership

State is owned according to its meaning and lifecycle, independently of the
mechanism used to represent it.

| State category | Owner | Architectural constraint |
| --- | --- | --- |
| Business records and authoritative lifecycle | Backend capability | Frontend snapshots never become an independent source of truth |
| Authentication condition | Authentication capability | Credentials and provider session objects do not leak into presentation models |
| Effective authorization | Access Control capability | Authorization is replaced atomically and is not reconstructed from role names, routes, or local storage |
| Interaction drafts | Owning interaction | Safe input survives recoverable failures; secrets are cleared according to their security lifecycle |
| Presentation preferences | Presentation boundary | Preferences cannot grant access or change business meaning |
| Application composition | Application boundary | Coordinates capability lifecycles without absorbing their rules |

The chosen state-management mechanism may evolve. A feature specification may
define observable transitions and consistency requirements, but it does not need
to prescribe a global store, context topology, cache library, or hook structure.

## 6. Cross-Cutting Responsibilities

Cross-cutting policies apply consistently without moving feature ownership into
shared infrastructure:

- **Accessibility:** interactions and feedback follow the frontend accessibility
  requirements; feature specifications add only capability-specific semantics.
- **Styling:** presentation follows the frontend styling policy and design
  system; feature specifications do not duplicate framework tutorials.
- **Testing:** feature specifications define observable scenarios; the frontend
  testing strategy owns test levels, responsibilities, and completion criteria;
  manifests and configuration own available tools and executable commands.
- **Security:** tokens, credentials, provider identities, and authorization data
  are exposed only to the narrow boundaries that require them.
- **Errors:** presentation distinguishes validation, authorization, concurrency,
  network, and service failures without exposing internal diagnostics.
- **Time:** business date, shift, event time, and system time remain distinct
  concepts wherever a capability presents them.
- **Audit-aware interaction:** correction reasons, expected versions, impact
  previews, and history are presented when required by the owning capability.

Shared presentation or infrastructure should be extracted only when reuse and
stable semantics justify it. Shared code must not become a place for unrelated
business policy.

## 7. Related Documents

- [Documentation Principles](../../../docs/dev-guide/documentation-principles.md)
- [Technology Baseline](../../../docs/architecture/technology-baseline.md)
- [Context Map](../../../docs/architecture/context-map.md)
- [System Overview](../../../docs/architecture/system-overview.md)
- [Ubiquitous Language](../../../docs/domain/ubiquitous-language.md)
- [Frontend Styling](../../../docs/dev-guide/frontend-styling.md)
- [Frontend Accessibility](../accessibility.md)
- [Frontend Testing Strategy](../testing/strategy.md)
- [Frontend Design System](../design-system/visual-identity.md)
- [Frontend Feature Specifications](../features/)

## 8. Scope Exclusions

This document does not define:

- source-tree structure, namespaces, filenames, or export conventions;
- component, hook, provider, or state-library choices;
- feature-specific pages, forms, state machines, or screen flows;
- exact routes, URLs, endpoints, payloads, or error codes;
- backend implementation, database, or persistence design;
- installed dependency versions or tooling adoption status; or
- temporary implementation gaps, migration plans, or backlog priority.
