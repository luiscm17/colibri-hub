---
document_type: baseline
status: active
implementation: implemented
scope: global
authority: explanatory
owner: architecture
last_reviewed: 2026-07-27
---

# Colibri Hub — Technology Baseline

> Verified technology stack present in the repository.
> Each entry is backed by dependency manifests, configuration files, or source code evidence.

---

## 1. Purpose

This document defines the technology baseline for Colibri Hub. It lists only what is verifiable from the repository state, separated by adoption level.

It does **not** define deployment providers, optional future infrastructure, or aspirational capabilities.

---

## 2. Implemented

Technology that is present in dependency manifests and actively used in source code.

### 2.1 Backend

| Technology | Version / Spec | Evidence |
|---|---|---|
| Python | 3.13 | `.python-version` |
| uv | workspace mode | `pyproject.toml` workspace config |
| FastAPI | ≥ 0.138.1 | `backend/pyproject.toml` |
| SQLAlchemy 2 | ≥ 2.0.51 | `backend/pyproject.toml`, ORM models in `warehouse.bales.adapters` |
| Psycopg | ≥ 3.3.4 (binary) | `backend/pyproject.toml` |
| Pydantic | via FastAPI + pydantic-settings ≥ 2.14.2 | Request/response models, `ApplicationSettings` |
| setuptools | src layout | `backend/pyproject.toml` build system |

### 2.2 Frontend

| Technology | Version / Spec | Evidence |
|---|---|---|
| React | ≥ 19.2.7 | `frontend/package.json` |
| TypeScript | ~6.0.2 | `frontend/package.json` devDependencies |
| Vite | ≥ 8.1.1 | `frontend/package.json` devDependencies, build tooling |
| Mantine | ≥ 9.4.1 (core, form, hooks, notifications) | `frontend/package.json` |
| pnpm | workspace with supply-chain policy | `frontend/pnpm-workspace.yaml` |
| react-router-dom | ≥ 7.18.1 | `frontend/package.json`, route definitions |
| react-data-grid | 7.0.0-beta.61 | `frontend/package.json`, `BaleDataGrid` component |
| ESLint | ≥ 10.6.0 | `frontend/package.json` devDependencies |
| PostCSS | ≥ 8.5.19 + mantine preset | `frontend/package.json` devDependencies |
| @tabler/icons-react | ≥ 3.44.0 | `frontend/package.json` |

### 2.3 Database and Migrations

| Technology | Evidence |
|---|---|
| PostgreSQL (via Supabase) | `supabase/config.toml`, migration files |
| Supabase CLI migrations | `supabase/migrations/` directory with timestamped SQL files |
| Row-Level Security (enabled) | Migration enables RLS on tables |

### 2.4 Architecture Style

| Aspect | Baseline |
|---|---|
| Domain modeling | DDD (bounded contexts, aggregates, value objects) |
| System structure | Hexagonal Architecture (ports/adapters in `warehouse.bales`) |
| Domain partitioning | Bounded contexts per architecture context map |

### 2.5 Root Workspace Tools

| Technology | Evidence |
|---|---|
| openpyxl | `pyproject.toml` root dependencies |
| pandas | `pyproject.toml` root dependencies |
| SQLAlchemy | `pyproject.toml` root dependencies (shared with backend workspace) |

---

## 3. Partial

Technology present in the repository but not fully adopted or complete.

| Technology | Current State | Gap |
|---|---|---|
| Authentication (frontend) | `AuthProvider` context, `useAuth` hook, `ProtectedRoute`, `LoginPage` | No backend auth middleware; frontend-only session |
| Supabase RLS | RLS enabled on tables, privileges revoked from `anon`/`authenticated`/`service_role` | No RLS policies defined; no runtime authorization flow |
| stdlib logging | `logging.getLogger(__name__)` in error handlers | No structured logging configuration or consistent usage |

---

## 4. Planned

Capabilities referenced in documentation or architecture plans but not yet present in source code.

| Capability | Status | Notes |
|---|---|---|
| Structured logging | Not implemented | Only basic stdlib `logging` import in one module |
| Audit trail | Not implemented | No audit tables, no event recording |
| Backend authorization (RBAC, scopes) | Design only | Planned `access` context not in codebase |
| Cache layer | Explicitly out of baseline | — |
| Queue / messaging | Explicitly out of baseline | — |
| Blob storage | Explicitly out of baseline | — |
| File import pipeline | Explicitly out of baseline | — |

---

## 5. Explicitly Not Present

Claims from prior documentation that are **incorrect** for this repository:

| Claim | Reality |
|---|---|
| Alembic for migrations | Repository uses Supabase CLI migrations (`supabase/migrations/`) |
| pytest | Not configured; tests use stdlib `unittest` |
| Pre-commit hooks | No `.pre-commit-config.yaml` or equivalent |
| CI/CD pipeline | No tracked CI configuration |

---

## 6. Testing Baseline

| Area | Tool | Scope |
|---|---|---|
| Backend unit tests | `unittest` (stdlib) | `backend/tests/` |
| Backend integration tests | `unittest` (stdlib) | `backend/integration_tests/` (requires local Supabase) |
| Frontend linting | ESLint | `pnpm lint` |
| Frontend type checking | TypeScript compiler | `tsc -b` via `pnpm build` |
| Frontend tests | None configured | No test runner or test framework |

---

## 7. Related Documents

| Document | Purpose |
|---|---|
| [System Overview](./system-overview.md) | System components, contexts, and principal flows |
| [Context Map](./context-map.md) | Bounded context boundaries, ownership, and handoffs |
