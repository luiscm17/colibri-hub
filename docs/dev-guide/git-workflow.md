---
document_type: runbook
status: active
implementation: not-applicable
scope: global
authority: normative
owner: architecture
last_reviewed: 2026-07-27
---

# Git Workflow

> Branch strategy, commit convention, pull request process, and code review
> guidelines for the Textile Production Management System.
>

---

## Quick Reference

| Topic | Rule |
|-------|------|
| **Base branch** | `main` — always stable, always deployable |
| **Branch format** | `<layer>/<short-topic>` — layer first, no type prefix |
| **Layer prefix** | `front/`, `back/`, `devops/`, `docs/` |
| **Commit format** | Conventional Commits — `type(scope): description` |
| **PR target** | `main` — always |
| **Merge strategy** | Squash merge (one commit per PR into `main`) |
| **Review required** | At least 1 approval before merge |
| **PR scope** | One concern per PR — split into stacked PRs if too large |

---

## 1. Branch Naming

### 1.1 Format

```
<layer>/<short-topic>
```

### 1.2 Layers

| Layer | When |
|-------|------|
| `front/` | Frontend code — UI components, forms, routing |
| `back/` | Backend code — API, services, data access, **migrations** |
| `devops/` | Infrastructure — CI/CD, Docker, config, scripts |
| `docs/` | Documentation — guides, READMEs, specs |

### 1.3 Rules

- Always lowercase, hyphens as separators.
- **2-3 words max** after the layer. If it needs more, the topic is too broad.
- Do NOT include issue tracker IDs.
- Delete the branch after merge.

### 1.4 Examples

| Branch | What it contains |
|--------|-----------------|
| `back/user-service` | User CRUD API + data layer |
| `front/settings-page` | User settings form UI |
| `front/login-page` | Login screen and auth UI |
| `back/auth` | Auth middleware, JWT, login endpoint |
| `back/payment-workflow` | Payment lifecycle logic |
| `front/status-badge` | UI badge showing entity state |
| `devops/docker-compose` | Docker setup for local dev |
| `devops/cd-pipeline` | Deployment pipeline config |
| `docs/git-workflow` | Git conventions guide |
| `front/order-form` | Order creation form + list |

---

## 2. Commit Convention (Conventional Commits)

Every commit message **must** follow the [Conventional Commits](https://www.conventionalcommits.org/) format.

### 2.1 Format

```
<type>(<scope>): <description>

[optional body]
```

### 2.2 Message characteristics

Every commit message **title** must follow these rules:

| Rule | Why |
|------|-----|
| **Imperative mood** — "Add shift form", not "Added" or "Adds" | Reads like an instruction, consistent with generated merge commits |
| **No period at the end** | Terse, scannable |
| **Max 200 characters** for the title | Long enough to capture the functional change without truncation |
| **Blank line before body** (if body exists) | Standard convention, tools rely on it |

```
# Good
feat(api): add user registration endpoint
fix(auth): validate token expiration on refresh

# Bad
feat(api): Added user registration endpoint.  ← past tense + period
feat(api): add user registration endpoint with email validation and welcome email  ← describes implementation, not functional change
refactor(api): rename UserService.py to account_service.py  ← names the file, not the functional change
```

### 2.3 Types

| Type | When to use |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or fixing tests |
| `docs` | Documentation only |
| `chore` | Maintenance, dependencies, tooling, config |
| `style` | Formatting, linting — no production code change |
| `perf` | Performance improvement |

### 2.4 Scope (optional but recommended)

The scope is the **module or domain** the change affects. Use one of:

| Scope | Area |
|-------|------|
| `auth` | Authentication and authorization |
| `api` | API design or contract changes |
| `ui` | Frontend / UI changes |
| `docs` | Documentation |
| `core` | Core domain logic and models |
| `db` | Database schemas and migrations |

### 2.5 Good examples

```
feat(api): add user registration with email verification
feat(ui): implement order creation form with validation
fix(auth): prevent session reuse after password change
refactor(api): extract notification service from user controller
test(core): cover payment workflow state transitions
docs: add git workflow and naming conventions
chore: configure eslint and prettier
```

### 2.6 Bad examples and why

| Bad commit | Problem |
|-----------|---------|
| `fix bug` | No type, no scope, too vague |
| `feat(warehouse): fix` | Type says feat, description says fix — inconsistent |
| `WIP` | Useless on its own; use `chore: wip` or squash before merge |
| `asdflkj` | Zero information |
| `refactor(db): replace schema.sql with migration-v2.sql` | Names the file instead of the functional change |

> **Principle — describe the functional change, not the file.**
> The title should answer **what changed in the system**, not which file was touched.
>
> | File | Functional change |
> |---|---|
> | `refactor(api): replace schema.sql` | `refactor(api): migrate from SQL schema to code-first migrations` |
> | `docs(db): remove outdated entity docs` | `docs(db): restructure DBML schemas per bounded context` |
> | `refactor(api): rename PaymentService.py` | `refactor(api): extract refund handling into independent module` |
>
> If it's hard to describe without naming files, the commit is probably not atomic.

### 2.7 Body (when to use)

Use the commit body when the change needs explanation:

```
feat(api): calculate order total automatically

Derive order total from line items - discount on the server side
as items are added. The client displays the running total.

Why server-side calculation?
- Single source of truth for pricing
- Prevents client-side manipulation
- Consistent with invoice generation
```

---

## 3. Daily Workflow

```bash
main ──► <layer>/xxx ──► commits ──► push ──► PR ──► review ──► merge ──► delete branch
```

### 3.1 Start a new branch

```bash
# Backend work
git checkout main && git pull
git checkout -b back/user-service

# Frontend work
git checkout main && git pull
git checkout -b front/settings-page

# Documentation
git checkout main && git pull
git checkout -b docs/git-workflow
```

### 3.2 Commit often, push when ready

```bash
# Make small, logical commits as you work
git add <files>
git commit -m "feat(ui): add user role selector to settings form"

# Push the branch (first time)
git push -u origin back/user-service

# Subsequent pushes
git push
```

### 3.3 Keep your branch up to date

```bash
git checkout main && git pull
git checkout back/user-service
git rebase main
```

**Always rebase, never merge `main` into your feature branch.** Rebasing keeps history linear and clean. If you have conflicts:

```bash
git rebase main
# resolve conflicts in each file
git add <resolved-file>
git rebase --continue
```

### 3.4 Open a Pull Request

1. Push your branch.
2. Open a PR on GitHub targeting `main`.
3. Fill the PR template (see section 4).
4. Mark as **Ready for review** (not Draft).
5. Assign at least one reviewer.

### 3.5 After merge

```bash
git checkout main && git pull
git branch -d back/user-service
```

---

## 4. Pull Request Process

### 4.1 Template

Each PR description **must** include:

```markdown
## Summary

<!-- One paragraph: what does this change do and why? -->

## Changes

- <!-- key changes, bullet points -->
```

### 4.2 Scope rule

Each PR should cover **one concern**. A concern is a single functional change — one feature, one fix, one refactor.

If a change is too large to fit in one focused PR, split it into stacked PRs:

- PR #1: `back/data-model` — domain logic and persistence
- PR #2: `back/api` — endpoints and validation
- PR #3: `front/form` — UI components

This protects reviewers from burnout and keeps reviews focused. There is no hard line-count limit — use judgment. If the PR description is hard to write without listing files, it's probably too broad.

### 4.3 Merge strategy

**Always squash merge** into `main`. This produces one clean commit per PR. The squashed commit message should match the PR title, formatted as a conventional commit:

```
feat(api): add user registration with email verification (#42)
```

Do NOT use "Create a merge commit" or "Rebase and merge" — they clutter history with intermediate commits.

### 4.4 Branch deletion

Delete the branch immediately after merge. GitHub offers a "Delete branch" button after merge — use it.

---

## 5. Code Review Guidelines

### 5.1 For the author

- Keep PRs small and focused (one concern per PR).
- Self-review before requesting review — catch your own oversights first.
- Respond to every comment. Even if you disagree, acknowledge and explain.
- If a comment is addressed in a new commit, mark it as resolved.
- Do not merge until all comments are resolved.

### 5.2 For the reviewer

- Review within 1 business day when possible.
- Focus on: correctness, maintainability, test coverage, edge cases.
- Distinguish between **blocking** and **non-blocking** comments:
  - **Blocking**: the PR must not merge without addressing this.
  - **Non-blocking**: suggestion, optional improvement. Use "nit:" prefix.
- Be constructive. Instead of "this is wrong", explain **why** and suggest **how**.

### 5.3 Review flow

```
Author opens PR
    │
    ▼
Reviewer reviews ──► Comments / Change requests
    │                       │
    ▼                       ▼
Approved             Author addresses feedback
    │                       │
    ▼                       ▼
Author merges        Author pushes new commits
                            │
                            ▼
                      Reviewer re-reviews
```

---

## 6. Integration with SDD

This project uses **Spec-Driven Development (SDD)**. The workflow integrates with Git as follows:

| SDD Phase | Git Action |
|-----------|------------|
| Proposal / Spec | No branch needed — documentation only |
| Design / Tasks | No branch needed — documentation only |
| Apply | Create branch, implement, commit |
| Verify | Tests pass, self-review, push — no separate branch |
| Archive | No branch — merge is done, branch deleted |
| PR | Open PR → review → squash merge → delete branch |

Each SDD change maps to **one branch** and **one squashed commit** in `main`. The branch layer follows where the change lives: `back/`, `front/`, `devops/`, or `docs/`.

---

## 7. Quick Reference Card (CLI)

```bash
# Start new work — pick the right layer
git checkout main && git pull
git checkout -b back/user-service     # backend
git checkout -b front/settings-page   # frontend
git checkout -b devops/docker-compose # infrastructure
git checkout -b docs/git-workflow     # documentation

# Commit
git add <files>
git commit -m "feat(api): add user list endpoint"

# Push
git push -u origin back/user-service

# Update branch with main
git checkout main && git pull
git checkout back/user-service && git rebase main

# After merge, clean up
git checkout main && git pull
git branch -d back/user-service
```
