---
document_type: architecture
status: active
implementation: partial
scope: backend/database
authority: explanatory
owner: backend
last_reviewed: 2026-07-27
---

# Colibri Hub — Persistence Design Principles

> Persistence-only design rules for backend data modeling.

---

## 1. Purpose and scope

This document defines the persistence-specific rules that later schema design
must preserve.

It is intentionally conceptual. It does **not** define tables, columns,
foreign keys, SQL, or ORM mappings.

---

## 2. Core persistence principles

1. **Persistence follows bounded-context ownership.** A context persists only
   the records whose business meaning it owns.
2. **Write models and traceability views stay separate.** Cross-context
   visibility is allowed; cross-context write-model flattening is not.
3. **Business truth and correction history stay separate.** Persistence must
   support editable current business state plus auditable correction history.
4. **Business time and system time stay separate.** Persist business date,
   shift, and system timestamps independently where the record meaning requires them.
5. **Persistence representation does not define aggregate shape.** Normalized
   header/detail records and historical physical names may remain for compatibility;
   map them explicitly to the current domain concepts instead of deriving a
   same-named aggregate from each table.

---

## 3. Reference and snapshot rule

Use **references** when the source remains authoritative and the consuming
context only needs linkage, validation, or current lookup.

Use **snapshots** when later source changes would rewrite the historical
meaning, evidence, or operator-readable context of the record.

### Stable rule

- Keep references for authoritative shared identities and canonical lookup data.
- Keep snapshots for business-critical descriptors when historical readability
  or audit evidence matters.
- Do not let catalog or upstream wording changes silently rewrite past business facts.

---

## 4. Read-model rule

A cross-context traceability or reporting model may combine data from multiple
contexts, but it must remain a **read model**.

### Stable rule

- Read models must not redefine write-model ownership.
- Read models must remain rebuildable from owning records.
- Read models must not become the canonical target for corrections or workflow transitions.

---

## 5. Correction and audit rule

Corrections are a persistence concern because current business truth must remain
editable under policy without losing historical traceability.

### Stable rule

- Keep current business state separate from correction history.
- Preserve at least actor, system timestamp, reason, and before/after values
  for every correction.
- Keep correction history owned by the same context that owns the corrected record.
- Do not force every correction into append-only duplicate business records when
  the domain requires controlled edits.

---

## 6. Time modeling rule

Where the domain distinguishes operational time from system-capture time,
persistence must keep them separate.

### Stable rule

- Do not infer business date from `created_at`.
- Persist shift explicitly when shift affects the meaning of the record.
- Preserve system timestamps independently for creation and correction history.
- When needed, preserve physical movement or occurrence time separately from
  system capture time.

---

## 7. Out of scope

This document does **not** define:

- tables, columns, or foreign keys
- SQLAlchemy model structure
- migration order
- partitioning or index strategy
- exact audit storage shape
- exact read-model projection mechanism
- final identifier formats
- concrete schema for stock balances, snapshots, or stage sequencing

---

## 8. Related documents

- [Backend Architecture Overview](../architecture/overview.md)
- [System Overview](../../../docs/architecture/system-overview.md)
