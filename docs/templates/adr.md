# ADR Template

Use this template when recording an architectural decision. Copy it to `docs/architecture/decisions/` and rename following the numbering convention: `NNN-short-decision-title.md`.

---

## Metadata Frontmatter

Replace the placeholder values below with actual content:

```yaml
---
document_type: adr
status: <draft|active|superseded|archived>
implementation: <not-started|partial|implemented|not-applicable>
scope: <context/capability>
authority: normative
owner: architecture
last_reviewed: <YYYY-MM-DD>
replaces: <path|null>
---
```

---

## ADR-NNN: [Decision Title]

### Status

[draft | active | superseded | archived]

If superseded, link to the replacing ADR.

### Context

Describe the problem, forces, or circumstances that make this decision necessary. Include relevant constraints, quality attributes, business drivers, and technical context.

### Decision

State the decision clearly and concisely. Use active voice: "We will..." or "The system shall..."

### Alternatives Considered

| Alternative | Pros | Cons | Reason Rejected |
|-------------|------|------|-----------------|
| [Option A]  | ...  | ...  | ...             |
| [Option B]  | ...  | ...  | ...             |

### Consequences

**Positive:**

- [Benefit or improvement gained]

**Negative:**

- [Tradeoff or cost accepted]

**Neutral:**

- [Side effect that is neither clearly positive nor negative]

### References

- [Related PRD, technical spec, or discussion](relative/path/to/document.md)
- [External resource or RFC](https://example.com)
