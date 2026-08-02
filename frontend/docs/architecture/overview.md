---
document_type: architecture
status: active
implementation: partial
scope: frontend
authority: explanatory
owner: frontend
last_reviewed: 2026-07-27
---

# Frontend Architecture Overview

Architectural reference for the Colibri Hub frontend application. This document
describes current implemented state, known gaps, and the approved target
architecture. Feature-specific implementation details live in
`frontend/docs/features/`.

---

## 1. Current State

### 1.1 Technology Stack (Verified)

| Layer | Technology | Version | Status |
| --- | --- | --- | --- |
| Framework | React | 19.x | Implemented |
| UI Library | Mantine | 9.x | Implemented |
| Forms | @mantine/form | 9.x | Implemented |
| Editable Grids | react-data-grid | 7.0.0-beta.61 | Implemented |
| Routing | react-router | 8.x | Implemented |
| Build Tool | Vite | 8.x | Implemented |
| Language | TypeScript | 6.x | Implemented |
| Styling | CSS Modules + Mantine props | — | Implemented |
| Icons | @tabler/icons-react | 3.x | Implemented |
| PostCSS | postcss-preset-mantine, postcss-simple-vars | — | Implemented |
| Linting | ESLint + typescript-eslint + react-hooks/refresh | — | Implemented |

### 1.2 Application Structure (Implemented)

```text
frontend/src/
├── app/                 # Shell: layout, providers, routes, navigation data
│   ├── layout/          # AppLayout, Sidebar, TopBar
│   ├── providers/       # Context providers (auth, theme)
│   └── routes/          # Route definitions and guards
├── common/              # Shared UI components and hooks (no business logic)
├── features/            # Feature modules by bounded context
│   ├── auth/            # Authentication flow
│   ├── warehouse/       # Raw material / finished product operations
│   ├── spinning/        # Yarn Spinning (code alias for Yarn Spinning context)
│   ├── lots/            # Lot Processing (code alias for Lot Processing context)
│   ├── reports/         # Cross-context reporting
│   ├── admin/           # Administrative screens
│   ├── profile/         # User profile
│   └── not-found/       # 404 handling
├── styles/              # Theme, global CSS, CSS Modules
├── assets/              # Static assets
├── main.tsx             # Entry point (Mantine, notifications, AuthProvider)
└── App.tsx              # Root component
```

### 1.3 Implemented Architectural Patterns

- **Feature-based organization**: each bounded context owns its pages,
  components, hooks, API calls, and types.
- **Composition over prop drilling**: compound components, context-based state,
  children/slot patterns.
- **Server state as primary**: business data fetched per-request, not duplicated
  in global stores. Local state for UI concerns only.
- **CSS Modules centralized in `src/styles/components/`**: component files
  contain only TSX; styling lives separately.
- **Theme as single source of truth**: all tokens defined via `createTheme` in
  `src/styles/theme/`, accessed through `var(--mantine-*)` in CSS Modules.
- **Path aliases**: `@/*` maps to `src/*` (Vite + tsconfig).
- **Barrel exports**: each feature exposes a clean public API via `index.ts`.
- **Lazy-loaded pages**: default exports on page components for `React.lazy()`.
- **No external state managers**: hooks + React context only.
- **No runtime CSS-in-JS**: Mantine 9 uses CSS Modules natively.

### 1.4 Frontend Responsibility Boundary

The frontend is a **client of backend APIs** and does not own domain meaning.
Authorization, business validation, state transitions, and policy decisions are
backend-authoritative. The frontend provides:

- Presentation logic (inline totals, previews, formatting)
- Local validation (completeness, format, immediate feedback)
- Capability-driven UI (actions enabled/disabled based on server responses)
- Audit-aware editing UX (correction reasons, edit windows, history visibility)

---

## 2. Gaps

### 2.1 Missing Infrastructure

| Gap | Impact | Priority |
| --- | --- | --- |
| No test framework configured | Cannot verify UI behavior or regressions | High |
| No API client layer conventions | Each feature ad-hoc fetches; no shared error/retry/auth patterns | High |
| No state management strategy documented for server cache | TanStack Query or similar not adopted | Medium |
| No accessibility testing or ARIA coverage validation | Compliance unknown | Medium |
| No internationalization (i18n) setup | All UI strings hardcoded in Spanish | Low |

### 2.2 Structural Gaps

| Gap | Description |
| --- | --- |
| Feature naming vs domain language | `lots/` used instead of `batch-processing/`; `spinning/` instead of `yarn-production/` — partial alignment with approved aliases |
| No `api/` directory at feature level uniformly | Some features have API modules, others fetch inline |
| No shared error handling pattern | ErrorBoundary exists but API error surfaces are inconsistent |
| No documented data-grid pattern | `react-data-grid` usage not standardized across features |
| Routes not aligned with bounded-context structure | Current route naming not verified against approved navigation model |

### 2.3 Authorization Integration Gap

Backend RBAC and capability-based authorization are not yet integrated into the
frontend. Current auth covers authentication (session/token), but
screen-level and action-level authorization from backend capabilities is not
wired.

---

## 3. Approved Target

### 3.1 Architecture Principles

1. **Mirror bounded contexts in navigation and code**: Warehouse, Yarn
   Spinning (`yarn-production`), Lot Processing (`batch-processing`), Access,
   and Reports as distinct feature areas with independent lifecycles.

2. **Backend authority over domain decisions**: the frontend never decides
   business validity — it reflects backend state and policy.

3. **Capability-driven authorization UI**: actions and screens derive visibility
   from backend capability metadata, not hardcoded role assumptions.

4. **Two input paradigms**: spreadsheet-style capture (high-volume, shift-end
   entry) and guided record forms (rich sequential workflows) — both supported
   as first-class patterns.

5. **Audit-aware editing**: records show editability state, correction windows,
   reason capture, and history. No silent rewrites.

6. **Context-aligned API modules**: each feature owns an `api/` boundary that
   maps to backend context endpoints.

### 3.2 Target Structure

```text
frontend/src/
├── app/                        # Shell, providers, router, navigation
├── features/
│   ├── warehouse/              # Raw material, identity, emission, PT, stock
│   ├── yarn-production/        # Section dashboards, discharge, quality, waste
│   ├── batch-processing/       # Lot queue, stage records, unified history
│   ├── access/                 # Auth + authorization UI
│   ├── reports/                # Cross-context consolidated views
│   └── catalogs/               # Shared reference data (admin/support)
├── common/
│   ├── components/             # Reusable UI primitives
│   ├── hooks/                  # Shared hooks
│   ├── grid/                   # Standardized data-grid components
│   └── feedback/               # Notifications, error surfaces
├── api/                        # Shared HTTP client, interceptors, types
└── styles/                     # Theme, global, CSS Modules
```

### 3.3 Target Conventions

- **Feature naming** uses approved code aliases: `warehouse`,
  `yarn-production`, `batch-processing`, `access`, `catalogs`.
- **API modules per context** aligned to backend bounded-context endpoints.
- **Server-cache layer** (e.g., TanStack Query) for fetch/cache/invalidate
  lifecycle — replacing ad-hoc fetch patterns.
- **Standardized data-grid pattern** documented and reused across Warehouse and
  Yarn Spinning features.
- **Testing strategy**: unit tests (Vitest) + component tests (Testing Library) + accessibility checks.
- **Authorization integration**: backend capabilities inform which actions and
  routes are available per user session.

### 3.4 State Management Target

| State Type | Owner | Pattern |
| --- | --- | --- |
| Server/business data | Backend (via API) | Server-cache library (fetch, cache, invalidate) |
| Form drafts | Local component | @mantine/form |
| Grid edits (pre-submit) | Local component | react-data-grid state |
| UI preferences (filters, panels) | Local/context | React state + context |
| Auth session | App-level provider | Context + token refresh |
| Authorization capabilities | App-level provider | Fetched from backend, cached in context |

### 3.5 Cross-Cutting Concerns (Target)

- **Error handling**: consistent surfaces for validation errors, auth failures,
  concurrency conflicts, network issues, and policy rejections.
- **Time semantics**: UI clearly distinguishes business date, shift, event
  time, and system timestamp — critical for shift-end capture workflows.
- **Controlled correction UX**: editing makes audit implications visible and
  respects backend correction-window policies.

---

## 4. Related Documents

- [Technology Baseline](../../../docs/architecture/technology-baseline.md)
- [Context Map](../../../docs/architecture/context-map.md)
- [System Overview](../../../docs/architecture/system-overview.md)
- [Frontend Design System](../design-system/visual-identity.md)
- [Frontend Features](../features/)

---

## 5. Scope Exclusions

This document does not define:

- Feature-specific page families or screen flows (see `frontend/docs/features/`)
- Component implementation details or API contracts
- Backend endpoint specifications
- Database or data-model design
- Exact route paths or URL structure
