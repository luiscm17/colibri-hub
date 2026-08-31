# Colibri Hub — Global Documentation

Comprehensive documentation index for the Colibri Hub platform. This directory contains cross-cutting, product-level, and architectural documentation. For implementation-specific docs, see [backend/docs/](../backend/docs/README.md) and [frontend/docs/](../frontend/docs/README.md).

## Product Requirements

Business capabilities, rules, and acceptance criteria.

- [Product Overview](./prd/product-overview.md) — Scope, actors, processes, transversal rules
- [PRD Index](./prd/README.md) — Full index of all capability PRDs
- **Warehouse**
  - [Warehouse Overview](./prd/warehouse/overview.md) — Area scope, responsibilities, dependencies
  - [Bale Management](./prd/warehouse/bale-management.md) — Reception, inventory, states, delivery
  - [Finished Product](./prd/warehouse/finished-product.md) — Finished goods management
  - [Production Supplies](./prd/warehouse/production-supplies.md) — Supply tracking
- **Operation**
  - [Operation Overview](./prd/operation/overview.md) — Area scope, actors, capabilities
  - [Yarn Spinning](./prd/operation/yarn-spinning.md) — Spinning process requirements
  - [Lot Processing](./prd/operation/lot-processing.md) — Lot processing requirements
  - [Lot Processing Records](./prd/operation/lot-processing-records.md) — Lot record-keeping
- [Access Control](./prd/access-control.md) — Authorization policy and RBAC
- [UI Requirements](./prd/ui-requirements.md) — Transversal product UI requirements

## Architecture

System-level decisions, technology stack, and context boundaries.

- [Architecture Index](./architecture/README.md) — Full architecture navigation
- [System Overview](./architecture/system-overview.md) — Components, contexts, principal flows
- [Context Map](./architecture/context-map.md) — Context ownership, dependencies, handoffs
- [Technology Baseline](./architecture/technology-baseline.md) — Verified adopted technology
- [ADR Index](./architecture/decisions/README.md) — Architecture Decision Records

## Domain

Ubiquitous language and domain model definitions.

- [Ubiquitous Language](./domain/ubiquitous-language.md) — Canonical term definitions
- [Warehouse Domain](./domain/warehouse.md) — Warehouse bounded context model

## Data Models

Conceptual data models (exploratory — not the implemented schema).

- [Data Models Index](./data-models/README.md) — Conceptual model navigation

## Templates

Standard templates for new documentation.

- [PRD Template](./templates/prd.md) — Product Requirements Document
- [Technical Spec Template](./templates/technical-spec.md) — Technical Specification
- [ADR Template](./templates/adr.md) — Architecture Decision Record

## Roadmap

- [Roadmap](./roadmap.md) — Capability delivery roadmap

## Dev Guide

Conventions and workflows for developers.

- [Documentation Principles](./dev-guide/documentation-principles.md) — Business vocabulary rules for Core Documentation
- [Git Workflow](./dev-guide/git-workflow.md) — Branches, commits, PRs, code review
- [Naming Conventions](./dev-guide/naming-conventions.md) — Naming for files, code, database, API
- [Backend Runtime Configuration](./dev-guide/backend-runtime-configuration.md) — Environment and settings
- [Data Cleaning & Transformation](./dev-guide/data-cleaning-transformation-guide.md) — Data processing guide
