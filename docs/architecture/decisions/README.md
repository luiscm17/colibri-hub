# Architecture Decision Records (ADR)

Durable architectural decisions for the Colibri Hub system. Each ADR captures the context, decision, alternatives considered, and consequences.

## Template

Use [docs/templates/adr.md](../../templates/adr.md) when creating a new ADR.

## Decisions

| ADR | Title | Scope | Status |
| ----- | ------- | ------- | -------- |
| [001](001-supabase-migrations.md) | Supabase CLI for database migrations | platform/database | Active |
| [002](002-separate-spinning-lot-processing.md) | Separate bounded contexts for Yarn Spinning and Lot Processing | domain/operations | Active |
| [003](003-single-production-identity.md) | Single production identity defined by Warehouse | domain/warehouse | Active |
| [004](004-hexagonal-capability-packaging.md) | Hexagonal architecture with capability-first packaging | backend/architecture | Active |
| [005](005-reception-as-application-action.md) | Reception as application action, not domain aggregate | warehouse/bales | Active |
| [006](006-role-neutral-business-language.md) | Role-neutral business language across system boundaries | global | Active |
