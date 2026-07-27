---
document_type: adr
status: active
implementation: implemented
scope: backend/architecture
authority: normative
owner: architecture
last_reviewed: 2026-07-27
---

# ADR-004: Hexagonal Architecture with Capability-First Packaging

## Status

Active

## Context

The backend needs a clear separation between:

- **Domain logic** — business rules, aggregates, value objects
- **Application logic** — use cases, orchestration, command/query handling
- **Infrastructure** — persistence, HTTP, external services

Additionally, the project organizes code by business capability (e.g., `warehouse.bales`, `warehouse.inventory`) rather than by technical layer (e.g., `models/`, `services/`, `repositories/`).

The architecture must support:

- Testability without infrastructure (domain and application layers test in isolation)
- Swappable adapters (test doubles for unit tests, PostgreSQL for production)
- Clear dependency direction (inward: adapters → ports → application → domain)

## Decision

We will use the Hexagonal Architecture (ports and adapters) pattern with capability-first module packaging.

Module structure per capability:

```text
<context>/<capability>/
├── domain/          # Aggregates, entities, value objects, domain services
├── application/     # Use cases, commands, queries, application errors
├── ports/           # Repository interfaces, identity providers, transaction contracts
└── adapters/        # SQLAlchemy repositories, HTTP handlers, external integrations
```

Dependency direction is strictly inward:

```text
adapters → ports → application → domain
```

- `domain/` has zero imports from other layers
- `application/` imports from `domain/` and `ports/` only
- `ports/` defines abstract interfaces (protocols/ABCs)
- `adapters/` implements ports and depends on external libraries

## Alternatives Considered

| Alternative | Pros | Cons | Reason Rejected |
|-------------|------|------|-----------------|
| Layer-first packaging (`models/`, `services/`, `repos/`) | Familiar to Django/Rails developers, simple initial structure | Scatters a single capability across many directories, makes it hard to understand a feature in isolation, couples unrelated capabilities at the layer level | Does not scale with multiple bounded contexts. A developer working on bales should not navigate through shared `models/` and `services/` directories containing unrelated domain code. |
| Clean Architecture (strict 4-ring) | Well-documented, many examples | More layers than needed for this project's complexity, entities vs. use cases distinction adds ceremony without value given our domain model simplicity | Hexagonal achieves the same dependency inversion with fewer conceptual layers. The ports/adapters metaphor maps more naturally to our infrastructure swap needs (test doubles ↔ PostgreSQL). |

## Consequences

**Positive:**

- Each capability is self-contained — navigate one directory to understand the entire feature
- Domain and application logic test without any infrastructure
- Adapters are swappable (test doubles for unit tests, PostgreSQL adapter for production)
- New capabilities follow a predictable, repeatable structure

**Negative:**

- Slightly more boilerplate per capability (port interfaces, adapter wiring)
- Developers must understand dependency direction rules

**Neutral:**

- Bootstrap/composition root (`bootstrap/`) wires adapters to ports at application startup

## References

- [Backend architecture overview](../../../backend/docs/architecture/overview.md)
