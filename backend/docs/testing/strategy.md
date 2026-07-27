---
document_type: technical-spec
status: active
implementation: partial
scope: backend/testing
authority: explanatory
owner: backend
last_reviewed: 2026-07-27
---

# Testing Strategy

Testing approach for the Colibri Hub backend.

---

## 1. Framework

The backend uses Python's **stdlib `unittest`** exclusively. No pytest, no
coverage tool, no linter or formatter is configured.

## 2. Test Organization

### Unit Tests

Location: `backend/tests/`

Run all unit tests:

```bash
uv run --locked python -m unittest discover -s backend/tests -v
```

Run a specific module:

```bash
uv run --locked python -m unittest backend.tests.domain.test_core_contracts -v
```

Focus a class or method by appending its dotted name to the module command.

### Integration Tests

Location: `backend/integration_tests/`

Integration tests require a running local Supabase instance with migrations
applied.

```bash
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres \
  uv run --locked python -m unittest discover -s backend/integration_tests -v
```

Integration tests:

- Deliberately accept only `postgresql+psycopg` URLs
- Target loopback port `54322`, database `postgres`
- Are guarded: they skip or fail clearly when `TEST_DATABASE_URL` is absent
- Never fall back to `DATABASE_URL`

## 3. Test Doubles for Unit Testing

Unit tests use **test doubles** (stubs, mocks, fakes) from `backend/tests/support/doubles.py`
to satisfy port interfaces without a real database. There is no separate SQLite
adapter — the repository pattern allows injecting in-memory or stub implementations
directly into use cases for testing.

This means unit tests:

- Run without any database (no PostgreSQL, no SQLite)
- Use `unittest.mock` and custom doubles to simulate persistence
- Verify domain and application logic in isolation from infrastructure

## 4. Test Design Principles

- Tests use stdlib `unittest.TestCase`
- No mocking frameworks beyond `unittest.mock`
- Domain tests verify business rules in isolation
- Application tests verify use-case orchestration with test doubles
- Persistence tests verify ORM mapping and query correctness with controlled sessions
- Integration tests verify persistence behavior against real PostgreSQL

## 5. What Each Layer Tests

| Layer | Scope | Database Required |
|-------|-------|-------------------|
| Domain | Aggregates, value objects, invariants, state transitions | No |
| Application | Use cases, error translation, transaction orchestration | No (test doubles) |
| Persistence | ORM mapping, query projections, constraint translation | No (test doubles) |
| API | HTTP routes, request validation, response shape | No (TestClient) |
| Integration | Persistence + constraints against real PostgreSQL | Yes (local PostgreSQL) |

## 6. Running Before Commit

```bash
# Unit tests (no external dependencies)
uv run --locked python -m unittest discover -s backend/tests -v

# Integration tests (requires local Supabase running)
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres \
  uv run --locked python -m unittest discover -s backend/integration_tests -v
```

## 7. Related Documents

- [Backend Architecture Overview](../architecture/overview.md)
- [Migration Strategy](../database/migrations.md)
