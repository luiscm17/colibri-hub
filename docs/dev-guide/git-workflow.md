---
document_type: runbook
status: active
implementation: not-applicable
scope: global
authority: normative
owner: architecture
last_reviewed: 2026-08-08
---

# Git Workflow

> Branch strategy, commit convention, pull request process, and code review
> guidelines for Colibri Hub.
>
> This document is the project's convention reference. It follows the standard
> Conventional Commits convention, declares the project's variations, and lists
> what is explicitly not required. No external tooling is assumed; a plain Git
> GitHub workflow is enough.

---

## 0. Convention Model

The project follows a layered convention model. The standard (Conventional
Commits) provides the commit format; this document provides the project
variations. Where anything in this document differs from a generic
Conventional Commits guide, **this document wins**.

| Layer | Source | Scope |
|-------|--------|-------|
| Standard | Conventional Commits | Commit format `type(scope): description`, imperative mood, atomic work units |
| Project variations | This document | Branch contexts, PR template, merge strategy, explicit non-requirements |

### 0.1 Standard

- Commit format: `type(scope): description` (Conventional Commits —
  <https://www.conventionalcommits.org/>).
- Imperative mood, no trailing period, max 200 characters.
- Commit by work unit: a commit represents one deliverable behavior, fix,
  migration, or docs unit; tests stay with the code they verify.

### 0.2 Project variations

- **Branch format**: `<layer>/<context>-<topic>` — layer first, then the
  bounded-context alias and short topic (see §1.2), **no type prefix** (never
  `feat/x`, `fix/x`, and so on).
- **Context prefixes**: short aliases per bounded context — `wh`, `yarn`,
  `lots`, `access`, `cat`, `auth` (see §1.2).
- **PR template**: `Summary + Changes`; no issue linkage requirement.
- **Merge strategy**: always squash merge into `main`.

### 0.3 Explicit non-requirements

The repository has no automated PR validation. PRs do **not** require:

- A linked issue or a `Closes #N` reference.
- Any label convention (for example, `type:*` labels).
- Shellcheck or any script-linting gate.
- A branch name tied to a commit type.

Contributors only need to follow this document.

---

## Quick Reference

| Topic | Rule |
| ------- | ------ |
| **Base branch** | `main` — always stable, always deployable |
| **Branch format** | `<layer>/<context>-<topic>` — layer first, no type prefix |
| **Context prefix** | `wh`, `yarn`, `lots`, `access`, `cat`, `auth` (see §1.2) |
| **Commit format** | Conventional Commits — `type(scope): description` |
| **PR target** | `main` — always |
| **Merge strategy** | Squash merge (one commit per PR into `main`) |
| **Review required** | At least 1 approval before merge |
| **PR scope** | One concern per PR — split into stacked PRs if too large |

---

## 1. Branch Naming

### 1.1 Format

```
<layer>/<context>-<topic>
```

The layer is the technical artifact the change touches (backend, frontend,
docs, devops). The context is the bounded context the change belongs to —
for cross-cutting work, omit it. The short topic describes the functional
change — **not** the file or issue number.

### 1.2 Contexts

| Prefix | Bounded context | When |
| -------- | ----------------- | ------ |
| `wh` | Warehouse | Bale reception, bale management, stock, deliveries |
| `yarn` | Yarn Spinning | Spinning sections, ball winding, twisting, progress records |
| `lots` | Lot Processing | Production lots, lot continuity, batch processing |
| `access` | Access Control | Roles, scopes, permissions, administration, audits |
| `cat` | Shared Reference Data | Catalogs, master data, reference values |
| `auth` | Authentication | Identity, sessions, accounts, credentials |

Every branch starts with a layer. For a bounded-context change, follow the
layer with the context alias and the topic; for cross-cutting work, use the
layer followed by the topic only:

| Prefix | When |
| -------- | ------ |
| `front/` | Frontend shell, design system, routing, cross-cutting UI |
| `back/` | Backend composition root, cross-cutting API concerns |
| `devops/` | Infrastructure — CI/CD, Docker, config, scripts |
| `docs/` | Documentation — guides, READMEs, specs, research |

### 1.3 Rules

- Always lowercase, hyphens as separators.
- **2-3 words max** for the topic. If it needs more, the topic is too broad.
- Describe the functional change, **never the file** — applies to every layer,
  including `docs/` and `devops/` (use `docs/git-conventions`, not
  `docs/git-workflow`).
- Do NOT include issue tracker IDs.
- Delete the branch after merge.

### 1.4 Examples

| Branch | What it contains |
| -------- | ----------------- |
| `back/wh-bale-reception` | Bale reception API and persistence |
| `front/wh-bale-reception` | Bale reception UI (paired with the backend above) |
| `back/yarn-spinning-dashboard` | Spinning dashboard API |
| `front/lots-continuity` | Lot continuity tracking UI |
| `back/access-admin-module` | Access control administration backend |
| `front/access-admin-module` | Access control administration UI (paired) |
| `back/cat-master-data` | Shared reference data management |
| `back/auth-session-expiry` | Session expiry handling backend |
| `front/auth-session-expiry` | Session expiry handling UI (paired) |
| `devops/local-dev-setup` | Docker setup for local dev (cross-cutting) |
| `docs/git-conventions` | Git conventions review (cross-cutting) |
| `front/wh-order-form` | Order creation form + list (frontend layer) |

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
| ------ | ----- |
| **Imperative mood** — "Add shift form", not "Added" or "Adds" | Reads like an instruction, consistent with generated merge commits |
| **No period at the end** | Terse, scannable |
| **Max 200 characters** for the title | Long enough to capture the functional change without truncation |
| **Blank line before body** (if body exists) | Standard convention, tools rely on it |

```
# Good
feat(wh): add bale reception endpoint
fix(auth): validate token expiration on refresh

# Bad
feat(wh): Added bale reception endpoint.  ← past tense + period
feat(wh): add bale reception endpoint with grid, stock, delivery and audit  ← describes implementation, not functional change
refactor(wh): rename BaleService.py to bale_service.py  ← names the file, not the functional change
```

### 2.3 Types

| Type | When to use |
| ------ | ------------- |
| `feat` | A new feature |
| `fix` | A bug fix |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or fixing tests |
| `docs` | Documentation only |
| `chore` | Maintenance, dependencies, tooling, config |
| `style` | Formatting, linting — no production code change |
| `perf` | Performance improvement |

### 2.4 Scope (optional but recommended)

The scope is the **bounded context or area** the change affects. Use the same
controlled vocabulary as branch contexts and layers:

| Scope | Area |
|-------|------|
| `wh` | Warehouse — bales, reception, stock, deliveries |
| `yarn` | Yarn Spinning — sections, progress, winding |
| `lots` | Lot Processing — production lots, continuity |
| `access` | Access Control — roles, scopes, permissions, audits |
| `cat` | Shared Reference Data — catalogs, master data |
| `auth` | Authentication — identity, sessions, accounts |

Cross-cutting technical scopes, only for work that does not belong to a
bounded context (mirrors the branch layers in §1.2):

| Scope | Area |
|-------|------|
| `ui` | Frontend shell / design system (cross-cutting UI) |
| `infra` | Tooling, config, CI/CD, scripts |
| `docs` | Documentation only (cross-cutting) |

Do not use alternate or shortened spellings for the same context (for example,
never `warehouse` when the scope is `wh`, never `frontend` when the scope is
`ui`).

**A feature that touches a bounded context always uses the context scope,
regardless of the layer.** Use `feat(wh)` for the bale reception API and for
its UI; reserve `ui`, `infra`, and `docs` for cross-cutting work that does not
belong to a bounded context. The layer lives in the branch name and the PR
diff, not in the commit scope.

### 2.5 Good examples

```
feat(wh): add bale reception with editable grid
feat(wh): add order creation form with validation
fix(auth): prevent session reuse after password change
refactor(access): extract role lifecycle use cases
test(yarn): cover spinning section progress transitions
docs: add git workflow and naming conventions
chore(infra): configure eslint and prettier
```

### 2.6 Bad examples and why

| Bad commit | Problem |
| ----------- | --------- |
| `fix bug` | No type, no scope, too vague |
| `feat(warehouse): fix` | Type says feat, description says fix — inconsistent |
| `WIP` | Useless on its own; use `chore: wip` or squash before merge |
| `asdflkj` | Zero information |
| `refactor(db): replace schema.sql with migration-v2.sql` | Names the file instead of the functional change |

> **Principle — describe the functional change, not the file.**
> The title should answer **what changed in the system**, not which file was touched.
>
> | File | Functional change |
> | --- | --- |
> | `refactor(wh): replace schema.sql` | `refactor(wh): migrate from SQL schema to code-first migrations` |
> | `docs(wh): remove outdated entity docs` | `docs(wh): restructure domain models per bounded context` |
> | `refactor(access): rename roles_service.py` | `refactor(access): extract role lifecycle into independent use cases` |
>
> If it's hard to describe without naming files, the commit is probably not atomic.

### 2.7 Body (when to use)

Use the commit body when the change needs explanation:

```
feat(wh): calculate order total automatically

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
main ──► <layer>/<context>-<topic> ──► commits ──► push ──► PR ──► review ──► merge ──► delete branch
```

### 3.1 Start a new branch

```bash
# Warehouse backend work
git checkout main && git pull
git checkout -b back/wh-bale-reception

# Warehouse frontend work (paired with the backend branch)
git checkout main && git pull
git checkout -b front/wh-bale-reception

# Access control backend work
git checkout main && git pull
git checkout -b back/access-admin-module

# Cross-cutting documentation
git checkout main && git pull
git checkout -b docs/git-conventions
```

### 3.2 Commit often, push when ready

```bash
# Make small, logical commits as you work
git add <files>
git commit -m "feat(wh): add bale reception form"

# Push the branch (first time)
git push -u origin back/wh-bale-reception

# Subsequent pushes
git push
```

### 3.3 Keep your branch up to date

```bash
git checkout main && git pull
git checkout back/wh-bale-reception
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
git branch -d back/wh-bale-reception
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

- PR #1: `back/wh-data-model` — domain logic and persistence
- PR #2: `back/wh-api` — endpoints and validation
- PR #3: `front/wh-form` — UI components

A full-stack feature is **not** one branch — it is paired branches with the
same topic, one per layer (`back/wh-bale-reception` + `front/wh-bale-reception`).
Each layer stays focused; the shared topic links them.

This protects reviewers from burnout and keeps reviews focused. There is no hard line-count limit — use judgment. If the PR description is hard to write without listing files, it's probably too broad.

### 4.3 Merge strategy

**Always squash merge** into `main`. This produces one clean commit per PR. The squashed commit message should match the PR title, formatted as a conventional commit:

```
feat(wh): add bale reception with editable grid (#42)
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
| ----------- | ------------ |
| Proposal / Spec | No branch needed — documentation only |
| Design / Tasks | No branch needed — documentation only |
| Apply | Create branch, implement, commit |
| Verify | Tests pass, self-review, push — no separate branch |
| Archive | No branch — merge is done, branch deleted |
| PR | Open PR → review → squash merge → delete branch |

Each SDD change maps to **one or more branches** and **one squashed commit per PR** in `main`. The branch follows the same rule as §1: a bounded context under a layer (`back/wh-bale-reception`, `front/wh-bale-reception`) or a cross-cutting layer (`front/`, `back/`, `devops/`, `docs/`).

---

## 7. Quick Reference Card (CLI)

```bash
# Start new work — pick layer, then context-topic
git checkout main && git pull
git checkout -b back/wh-bale-reception      # warehouse backend
git checkout -b front/access-admin-module   # access control frontend
git checkout -b devops/local-dev-setup      # infrastructure (cross-cutting)
git checkout -b docs/git-conventions        # documentation (cross-cutting)

# Commit
git add <files>
git commit -m "feat(wh): add bale reception API"

# Push
git push -u origin back/wh-bale-reception

# Update branch with main
git checkout main && git pull
git checkout back/wh-bale-reception && git rebase main

# After merge, clean up
git checkout main && git pull
git branch -d back/wh-bale-reception
```
