---
document_type: runbook
status: active
implementation: implemented
scope: global
authority: normative
owner: architecture
last_reviewed: 2026-07-27
---

# Naming Conventions

> Consistent naming rules for directories, files, modules, functions, variables,
> database objects, and API endpoints.

---

## Quick Reference

| Scope | Python | JavaScript / TypeScript |
|-------|--------|------------------------|
| **Directories** | `snake_case` (packages), `kebab-case` (non-package) | `kebab-case`, singular |
| **Source files** | `snake_case.py` | `camelCase.ts` / `PascalCase.tsx` |
| **Test files** | `test_{name}.py` | `{name}.test.ts` |
| **Packages / Modules** | package dir + `__init__.py` | ES module, file name = module name |
| **Functions** | `snake_case()` | `camelCase()` |
| **Variables** | `snake_case` | `camelCase` |
| **Constants** | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |
| **Classes** | `PascalCase` | `PascalCase` |
| **Database tables** | `snake_case`, plural | — |
| **Database columns** | `snake_case`, singular | — |
| **API endpoints** | `kebab-case`, plural nouns | — |
| **Environment vars** | `UPPER_SNAKE_CASE` | — |

---

## 1. Directories

### 1.1 Rules

- **Non-package directories** → `kebab-case`, all lowercase (docs, config, CI, etc.).
- **Python package directories** → `snake_case`, all lowercase. Python imports require valid identifiers — hyphens are not valid.
- **JS/TS directories** → `kebab-case`, all lowercase.
- **Singular nouns** — no plurals. Exceptions: clearly collective like `tests/`, `fixtures/`, `mocks/`.
- Short — prefer one or two words. Three max.
- Group by **domain** or **feature**, not by technology.

### 1.2 Structure example

```
project/
├── domain/                  # grouped by domain / feature
│   ├── models.py
│   ├── services.py
│   ├── views.py
│   └── tests/
│       ├── test_models.py
│       └── test_services.py
├── shared/                  # cross-domain utilities
│   ├── auth/
│   └── middleware/
├── config/
├── scripts/
└── docs/
```

The directory layout depends on the framework and architecture. Use these rules as guidance, not dogma.

### 1.3 Anti-patterns

| Wrong | Why |
|-------|-----|
| `src/` (top-level) | Tells nothing about the content |
| `utils/` | Dumping ground — always split by concern |
| `my-package/` | Hyphens in Python package names break imports: use `snake_case` |
| `feature/` | Flat by layer, not by domain — doesn't scale |
| `Controllers/` | PascalCase in directory names |
| `misc/`, `helpers/`, `common/` | Vague names that accumulate unrelated code |

---

## 2. Files

### 2.1 Rules

| Context | Convention | Example |
|---------|-----------|---------|
| **Python files** | `snake_case.py` | `user_service.py` |
| **JS/TS files** | `camelCase.ts` / `PascalCase.tsx` | `userForm.tsx` `UserForm.tsx` |
| **Test files (Python)** | `test_{name}.py` | `test_user_service.py` |
| **Test files (JS/TS)** | `{name}.test.ts` | `userForm.test.tsx` |
| **Config files** | `kebab-case` | `docker-compose.yml` |
| **Documentation** | `kebab-case.md` | `contributing.md` |
| **Python package init** | `__init__.py` | `domain/__init__.py` |

One primary concern per file — do not put models, views, and services in the same file.

### 2.2 Examples

```
# Python
user_service.py
test_user_service.py
models.py
serializers.py
views.py

# React (TS)
userForm.tsx
userForm.test.tsx
userList.tsx
useUserForm.ts
useUsers.ts

# Vue
UserForm.vue
UserForm.spec.ts
userForm.css

# Config
docker-compose.yml
.eslintrc.json
vite.config.ts

# Docs
contributing.md
```

---

## 3. Modules / Packages

### 3.1 Rules

| Context | Convention | Example |
|---------|-----------|---------|
| **Python package** | `snake_case` dir + `__init__.py` | `from domain import services` |
| **JS/TS module** | `camelCase` file | `import { useForm } from './useForm'` |
| **Python internal** | `_prefix` for private modules | `_helpers.py` |
| **Directory = package** | Package name matches directory | `domain/` → `import domain` |

### 3.2 Python

```python
# Internal imports
from domain import services, models
from domain.services import calculate_total

# Explicit is better than implicit
from domain.services import calculate_total
from domain.models import User
```

### 3.3 JavaScript / TypeScript

```ts
// Named exports — prefer named over default
import { useForm } from './hooks/useForm'
import { FormComponent } from './components/formComponent'
import { api } from './services/api'

// Barrel exports via index.ts
export { useForm } from './useForm'
export { useData } from './useData'
```

### 3.4 Domain entities: flat → package transition

In Hexagonal / DDD projects, domain entities grow over time. Use this rule:

- **Start flat**: a single `snake_case.py` file when the entity has no value objects, events, or services of its own.
  ```
  shared/domain/user.py          # from shared.domain.user import User
  ```

- **Promote to package** once the entity needs value objects, events, or grows past ~200 lines.
  ```
  user/
  ├── __init__.py        # Re-exports public API
  ├── user.py            # Entity class
  ├── events.py          # UserCreated, UserRoleChanged
  └── value_objects.py   # UserRole, Email
  ```

- **The `__init__.py` is the facade.** It re-exports so consumers import from the package, never from the internal module:
  ```python
  # user/__init__.py
  from .user import User
  from .events import UserCreated
  from .value_objects import UserRole

  # Consumer — never sees the internal module name
  from shared.domain.user import User, UserRole
  ```

- **Scope the package on actual complexity.** Do not create the directory until you need it. A flat file is cheaper to navigate and rename. This rule is Python-specific. TypeScript achieves the same with `index.ts` barrel files.

---

## 4. Functions and Methods

### 4.1 Rules

| Context | Convention | Example |
|---------|-----------|---------|
| **Python** | `snake_case()` | `calculate_total()` |
| **JavaScript / TypeScript** | `camelCase()` | `calculateTotal()` |
| **Classes (both)** | `PascalCase` | `UserService`, `FormComponent` |
| **Private Python** | `_prefix` | `_validate_input()` |
| **Private JS/TS** | `#` or `_` per project | `#validateInput()` |

- **Verb + Noun**: `calculate_total()`, `find_user_by_id()`, `authorize_payment()`.
- Reveal **intent**, not implementation. `get_data()` is meaningless without context.
- Boolean functions read as questions: `is_valid()`, `has_permission()`, `can_edit()`.

### 4.2 Examples

```python
# Python — good
def calculate_total(gross: float, discount: float) -> float
def find_user_by_id(user_id: int)
def authorize_payment(payment_id: int)
def is_valid_email(email: str) -> bool

# Python — bad
def getData()              # snake_case required
def process()              # Process what?
def check()                # Check what? Be specific
```

```ts
// TypeScript — good
function calculateTotal(gross: number, discount: number): number
function findUserById(userId: number)
function authorizePayment(paymentId: number)
function isValidEmail(email: string): boolean

// TypeScript — bad
function get_data()        # camelCase required
function handler()         # Handler what? Be specific
```

---

## 5. Variables and Constants

### 5.1 Variables

| Context | Convention | Example |
|---------|-----------|---------|
| **Python** | `snake_case` | `total_amount`, `user_id` |
| **JavaScript / TypeScript** | `camelCase` | `totalAmount`, `userId` |

Descriptive, no abbreviations unless universally known. No single-letter variables except loop indices (`i`, `j`) and very short scopes.

```python
# Python — good
total_amount
net_price
user_id
created_at

# Python — bad
ta          # What is ta? Total amount? Tax applied?
uid         # User ID? Unique ID? Nobody knows
tmp         # Always a sign you don't know what to name it
data        # Everything is data — be specific
```

```ts
// TypeScript — good
const totalAmount: number
const netPrice: number
const userId: number
const createdAt: Date
```

### 5.2 Constants

**`UPPER_SNAKE_CASE`** everywhere — Python and JS.

```python
# Python
MAX_FILE_SIZE = 10_485_760
DEFAULT_PAGE_SIZE = 25
STATUS_ACTIVE = "active"
```

```ts
// TypeScript
const MAX_FILE_SIZE = 10_485_760
const DEFAULT_PAGE_SIZE = 25
const STATUS_ACTIVE = 'active' as const
```

**Exceptions:**

- Framework conventions (e.g. Django settings: `SESSION_COOKIE_AGE`, `AUTH_USER_MODEL`).
- React/JSX constants that are components → `PascalCase` (`DefaultAvatar`, `LoadingSpinner`).

### 5.3 Boolean naming

Prefix booleans with `is`, `has`, `can`, `should`, `needs`:

```python
# Python
is_active
has_permission
can_edit
needs_review
should_refresh
```

```ts
// TypeScript
const isActive: boolean
const hasPermission: boolean
const canEdit: boolean
```

---

## 6. Database

### 6.1 Table names

- **`snake_case`**, **plural** nouns.
- Prefix by domain when needed to avoid collisions.

```
users
user_roles
orders
order_items
```

### 6.2 Column names

- **`snake_case`**, singular.
- Include the unit in the name when ambiguous.

```
total_amount_cents
user_id
created_at
updated_at
created_by
```

### 6.3 Primary and foreign keys

| Convention | Example |
|-----------|---------|
| Primary key | `id` (auto-increment / UUID) |
| Foreign key | `{referenced_table}_id` |
| Timestamps | `created_at`, `updated_at` (UTC) |

---

## 7. API Endpoints

### 7.1 Rules

- **`kebab-case`**, **plural** nouns.
- Versioned from day one (`/api/v1/`).
- RESTful: use HTTP methods, not verbs in the URL.
- Keep resource hierarchy flat — avoid deep nesting.

### 7.2 Examples

```
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/{id}
PUT    /api/v1/users/{id}
DELETE /api/v1/users/{id}

GET    /api/v1/users/{id}/orders
POST   /api/v1/users/{id}/orders

POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
```

### 7.3 Anti-patterns

```
GET  /api/getUsers               # camelCase in URL + verb
POST /api/create-user             # Verb in URL — POST already means create
GET  /api/v1/userDetails          # PascalCase + plural missing
POST /api/v1/user/orders          # Singular resource
GET  /api/v1/users/get-all        # Verb in URL
```

---

## 8. Environment Variables

### 8.1 Rules

- **`UPPER_SNAKE_CASE`**.
- Prefix with the project or application name.
- Group related variables with common prefixes.

```
APP_NAME_DB_HOST=localhost
APP_NAME_DB_PORT=5432
APP_NAME_DB_NAME=my_app
APP_NAME_DB_USER=admin
APP_NAME_DB_PASSWORD=

APP_NAME_API_PORT=8080
APP_NAME_ENV=development

APP_NAME_JWT_SECRET=
APP_NAME_JWT_EXPIRY_HOURS=24
```

---

## 9. Summary

| Context | Convention | Rule of thumb |
|---------|-----------|---------------|
| Directory | `snake_case` (Python packages), `kebab-case` (others) | singular, domain-grouped |
| Python file | `snake_case.py` | one concern per file |
| JS/TS file | `camelCase.ts` / `PascalCase.tsx` | components get PascalCase |
| Python test | `test_{name}.py` | matches source |
| JS/TS test | `{name}.test.ts` | matches source |
| Python function | `snake_case()` | verb + noun, reveal intent |
| JS/TS function | `camelCase()` | verb + noun, reveal intent |
| Python variable | `snake_case` | descriptive, no abbreviations |
| JS/TS variable | `camelCase` | descriptive, no abbreviations |
| Constant | `UPPER_SNAKE_CASE` | both Python and JS |
| Class | `PascalCase` | both Python and JS |
| Database table | `snake_case`, plural | domain prefix |
| Database column | `snake_case`, singular | include unit |
| API endpoint | `kebab-case`, plural | versioned, RESTful |
| Env var | `UPPER_SNAKE` | project prefix |

---

> When in doubt, prefer the **longer, descriptive name** over a short ambiguous one.
> Code is read far more often than it is written — optimize for the reader.
