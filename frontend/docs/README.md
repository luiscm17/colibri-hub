# Frontend Documentation

Use this index to find the document that owns a frontend decision. Project and
product requirements remain authoritative for business behavior; frontend
feature specifications project those requirements into presentation and
interaction contracts.

| Document | Owns |
| --- | --- |
| [Frontend Architecture Overview](architecture/overview.md) | Durable responsibilities, boundaries, and dependency direction |
| [Technology Baseline](../../docs/architecture/technology-baseline.md) | Technology choices that materially constrain the architecture |
| [Visual Identity](design-system/visual-identity.md) | Visual principles and semantic token definitions |
| [Frontend Styling](../../docs/dev-guide/frontend-styling.md) | Policy for applying tokens and styles |
| [Accessibility Guidelines](accessibility.md) | Transversal accessibility requirements and validation responsibilities |
| [Testing Strategy](testing/strategy.md) | Test levels, responsibilities, coverage, and automation/manual boundaries |
| [Editable Batch Grid](patterns/editable-batch-grid.md) | Reusable batch-editing interaction contract and adoption obligations |
| [Feature Specifications](features/) | Capability-specific presentation, interaction, transport, and acceptance scenarios |

Start with the feature specification for the capability being changed, then
follow its references to the relevant transversal owners. Do not restate shared
policy in feature documents.
