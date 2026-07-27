# Domain Research

> Research documents organized by business domain. Each document captures
> findings from investigating existing systems, processes, and data sources
> to inform system design and requirements.

> **⚠️ Isolation boundary:** Research documents provide evidence and analysis only.
> They do NOT define normative business rules, domain models, or architecture.
> References to PRD, domain, or architecture docs are citations for context — not
> authority claims. The normative sources are the PRDs, domain maps, and ADRs themselves.

---

## Warehouse (Almacén)

Research into the warehouse domain within the Production Management system:
receiving, storage, inventory, supplies, and the relationship with Operation.

| Document                                          | Description                                                                                                               | SIC JAC  TABLE DB                |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| [SIC JAC Reports](warehouse/sic-jac-reports.md)   | Structure and fields of SIC JAC inventory reports: codification, categories, sub-categories, entries, exits, and balances | Reporte                          |
| [Finished Product](warehouse/finished-product.md) | Finished product flow: delivery, stock, recovered/defective product, sales exits                                          | 06 Prducto Terminado 2020        |
| empty                                             | empty                                                                                                                     | 07 Almacen Ovillos               |
| empty                                             | empty                                                                                                                     | 08 Distribuidora Illampu         |
| [Dyehouse](warehouse/dyehouse.md)                 | Dyehouse (tintorería) report structure: dyes, chemical supplies, movement tracking                                        | 09 Almacen Tintoreria y Quimicos |
| empty                                             | empty                                                                                                                     | 10 Pedidos de Clientes           |
| [Bags and Labels](warehouse/bags-and-labels.md)   | Bags and labels subsystem within SIC JAC: categories, suppliers, stock control by units                                   | 11 Bolsas y Etiquetas            |
| empty                                             | empty                                                                                                                     | 12 Planta Illampu Textiles       |
| empty                                             | empty                                                                                                                     | 17 Almacen de Materia Prima      |

---

## Operation (Operación)

_No research documents yet._

---

## Administration

_No research documents yet._

---

## Architecture & Design

| Document | Description |
|----------|-------------|
| [RBAC Design](rbac-design.md) | RBAC authorization model with hierarchical scopes, inspired by Azure RBAC. Role definitions (`staff`, `lead`, `manager`, `director`, `executive`, `sysadmin`), resource types, scope tree, assignment exceptions, and mapping to the current organizational structure. |
