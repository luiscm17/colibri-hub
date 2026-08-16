---
document_type: baseline
status: active
scope: global
authority: explanatory
owner: architecture
---

# Colibri Hub - Technology Baseline

## 1. Purpose

This document records the technology choices that materially constrain the
architecture of Colibri Hub. A technology belongs in this baseline when
replacing it would change the application model, a major integration boundary,
data ownership, the security model, or the operating workflow.

This is not a dependency inventory. Package manifests, lockfiles, runtime
configuration, and source code remain authoritative for exact versions,
transitive dependencies, plugins, build utilities, and implementation status.

The baseline therefore favors stable technology families and architectural
consequences over package names that are incidental or replaceable within an
existing boundary.

## 2. Application Platforms

### 2.1 Backend

| Choice | Architectural consequence |
| --- | --- |
| Python | Backend capabilities use the Python runtime and ecosystem. Runtime compatibility is governed by the repository configuration. |
| FastAPI | The backend exposes HTTP application boundaries through ASGI and typed request and response contracts. Business policy remains independent of the web framework. |
| SQLAlchemy | Persistence adapters use explicit relational mapping and transaction boundaries. Domain and application policy do not depend on ORM records. |

Supporting drivers, validation packages, build tools, and workspace managers are
implementation dependencies. Their exact selection and versions are owned by
the backend and root manifests unless they introduce a separate architectural
constraint.

### 2.2 Frontend

| Choice | Architectural consequence |
| --- | --- |
| React with TypeScript | The frontend is a typed browser application built from declarative presentation and interaction boundaries. Feature contracts remain independent of component topology and state-management mechanism. |
| Mantine | Mantine provides the adopted visual primitives and theming foundation. Feature code follows the frontend styling and design-system policies; optional Mantine packages may be adopted when a concrete interaction requires them. |
| Supabase browser client | Authentication integrates with the configured identity provider through its browser client. Provider sessions and tokens remain isolated behind the Authentication boundary. |

Routing, icons, editable grids, form helpers, linting, CSS processing, build
plugins, and similar packages support the frontend implementation but do not
define its architecture. They may evolve or be replaced while the frontend
responsibilities and contracts remain stable.

## 3. Data and Platform Boundaries

| Choice | Architectural consequence |
| --- | --- |
| PostgreSQL | Authoritative application data is persisted relationally with database-enforced integrity. Backend capabilities own database access; the browser does not access application tables directly. |
| Supabase platform | The project uses Supabase for the local PostgreSQL and Authentication environment. Administrative credentials never cross into the browser boundary. |
| Imperative SQL migrations | Schema evolution is represented by ordered SQL migrations. Persistence mappings and migrations must evolve together. |

Database extensions and platform services belong in this baseline only when a
product capability depends on them as an architectural boundary. Merely being
available from the platform is not sufficient.

## 4. Toolchain and Version Ownership

Exact versions and package availability are intentionally excluded from this
document. They are governed by:

| Concern | Authoritative evidence |
| --- | --- |
| Python runtime and dependencies | `.python-version`, `pyproject.toml`, `backend/pyproject.toml`, and `uv.lock` |
| Frontend runtime and dependencies | `frontend/package.json`, `frontend/pnpm-lock.yaml`, and `frontend/pnpm-workspace.yaml` |
| Database capabilities | `supabase/config.toml` and ordered files under `supabase/migrations/` |
| Available verification commands | Repository agent guidance and the relevant testing strategy |

A package being absent does not prohibit its later adoption. A package being
present does not make it an architectural requirement. Adoption decisions are
driven by capability needs and must preserve the boundaries defined by the
architecture and feature specifications.

## 5. Exclusions

This baseline does not track:

- exact dependency versions or release ranges;
- transitive dependencies, plugins, formatters, linters, icons, or build helpers;
- namespaces, directories, modules, classes, or component structure;
- temporary implementation gaps or partially completed capabilities;
- planned, optional, or merely available infrastructure;
- backlog priorities or migration status; or
- claims that a library is mandatory solely because it is currently installed.

Testing levels and responsibilities belong to the backend and frontend testing
guidance. Visual tokens and styling rules belong to the corresponding frontend
design-system and styling documents.

## 6. Related Documents

| Document | Purpose |
| --- | --- |
| [System Overview](./system-overview.md) | System responsibilities and principal flows |
| [Context Map](./context-map.md) | Capability boundaries, ownership, and handoffs |
| [Frontend Architecture](../../frontend/docs/architecture/overview.md) | Frontend responsibilities and dependency direction |
| [Frontend Visual Identity](../../frontend/docs/design-system/visual-identity.md) | Visual principles and semantic tokens |
| [Frontend Testing Strategy](../../frontend/docs/testing/strategy.md) | Frontend test levels and responsibilities |
