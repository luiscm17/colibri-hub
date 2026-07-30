---
document_type: technical-spec
status: active
implementation: partial
scope: warehouse/bales
authority: explanatory
owner: backend
last_reviewed: 2026-07-28
---

# Technical Specification — Backend Bale Management

> **Normative PRD:** [Bale Management](../../../docs/prd/warehouse/bale-management.md)

**Product:** Colibri Hub  
**Context:** Warehouse  
**Type:** Technical Specification — Backend  
**Status:** Partially implemented  
**Technical baseline:** Repository `luiscm17/colibri-hub`, branch `main`, commit `447ee79`  
**Complementary spec:** Frontend bale management technical specification  
**Date:** 2026-07-28

---

## 1. Executive summary

> This document is a **technical specification** describing how the backend implements the bale management capability. Business rules and acceptance criteria are defined in the [normative PRD](../../../docs/prd/warehouse/bale-management.md); this specification details the implementation approach, API contracts, and architecture.

The Warehouse backend already supports registering a raw-material batch and all its bales through a transactional operation. The capability is implemented with FastAPI, Pydantic, SQLAlchemy, PostgreSQL, and Supabase migrations, following a hexagonal architecture scoped to `warehouse.bales`.

This technical specification defines the evolution required to complete the bale management flow consumed by the frontend:

1. Adjust the existing batch registration to work with a business date and a summary response.
2. Query aggregated stock indicators through filters.
3. Query a single bale by its composite business identity (`shipment_number + bale_number`).
4. Deliver one or more bales to Production in a single batch operation with per-bale results.

The scope preserves the current business model: bales are discrete units, delivered whole, `delivered` means delivered to and used by Production, and no reversals or additional states exist.

## 2. Current backend state

> **Implementation status**: This section describes both the **current implementation** and the **target state**. Section 2.1 documents what is already built; section 2.2 lists the gaps that remain to reach the target state defined in the normative PRD.

### 2.1 Available capabilities

The repository currently contains:

- Endpoint `POST /api/v1/warehouse/bales`.
- Atomic registration of a `RawMaterialBatch` header and one or more `Bale` records.
- Global identification of the batch via `shipment_number`.
- Business identity of the bale via `shipment_number + bale_number`.
- Uppercase normalization of `shipment_number`, `bale_number`, and `material_type`.
- States `in_warehouse` and `delivered`.
- Domain rule `Bale.deliver()` for the irreversible transition to `delivered`.
- Net weight calculation in the domain as gross weight minus container weight.
- Repository, identity, and transaction ports.
- SQLAlchemy adapters and FastAPI dependency composition.
- Tables `raw_material_batches` and `raw_material_bales`.
- Named integrity constraints, batch index, RLS enabled, and privileges revoked.
- Common error contract with `code`, `message`, and `fields`.
- Unit tests with `unittest` and guarded PostgreSQL integration tests.

### 2.2 Gaps relative to target state

| Area | Current state | Target state |
| --- | --- | --- |
| Reception date | Datetime with timezone (`datetime` / `timestamptz`) | Business date (`date` / `DATE`) |
| Bales per batch | One or more, no explicit maximum | Between 1 and 100 |
| Registration response | Includes all registered bales | Summary only with `bale_count` |
| Aggregate query | Not available | Filterable stock summary computed in PostgreSQL |
| Individual query | Not available | Lookup by shipment number and bale number |
| State update | Domain rule available, no use case or endpoint | Batch delivery endpoint with per-bale results |
| Repository reads | Insert only | Query projections and bale loading for transition |
| Browser integration | No CORS policy configured | Allowed origins via configuration |

## 3. Objectives

> For authoritative business rules, see the [normative PRD](../../../docs/prd/warehouse/bale-management.md).
> Objectives below reflect implementation targets derived from the PRD.

### 3.1 Functional objectives

- Register between 1 and 100 bales in a single transaction.
- Treat `received_at` as a business date without inventing a time component.
- Return a brief and stable registration response to the frontend.
- Compute aggregated counts and weights on persisted data in the backend.
- Unambiguously locate a bale with `shipment_number + bale_number`.
- Expose the complete data required by the detail screen.
- Deliver multiple bales in a single batch request with a shared business date.
- Allow only the `in_warehouse → delivered` transition.
- Report per-bale results including conflicts and not-found identities.

### 3.2 Technical objectives

- Extend the existing `warehouse.bales` capability boundary.
- Preserve the hexagonal architecture dependency direction.
- Reuse the already-implemented domain behavior for delivery.
- Separate write commands from read queries without introducing a CQRS platform.
- Preserve decimal precision across input, persistence, computation, and responses.
- Protect registration atomicity and state-transition exclusivity.
- Document all contracts via OpenAPI and automated tests.

## 4. Scope

> For authoritative business rules, see the [normative PRD](../../../docs/prd/warehouse/bale-management.md).
> Scope boundaries below describe the technical implementation scope.

### 4.1 Included

- Adjustments to the existing registration endpoint.
- Migration of `received_at` to date type.
- Aggregate stock summary endpoint.
- Individual detail endpoint.
- Batch delivery endpoint (multiple bales, single request, per-bale results).
- New use cases, ports, adapters, HTTP models, and composition.
- Error contract extension.
- Indexes required for approved queries.
- CORS configuration for the web application.
- Domain, application, persistence, HTTP, OpenAPI, and PostgreSQL integration tests.
- Update of affected technical and business documentation.

### 4.2 Out of scope

- Authentication, RBAC, and per-user authorization policies.
- Backend integration with Supabase Auth.
- New bale states.
- Partial deliveries.
- Returns to warehouse.
- Movement history or audit trail.
- Responsible actor, destination, or delivery reference.
- General or paginated bale listing.
- Editing weights, material, dtex, provider, batch, or bale number.
- Deletion of batches or bales.
- Production-context metrics other than `delivered` status.
- Totals sent by the frontend during registration.

## 5. Business rules

> For authoritative business rules, see the [normative PRD](../../../docs/prd/warehouse/bale-management.md).
> The rules below are reproduced for implementation reference. The [normative PRD](../../../docs/prd/warehouse/bale-management.md) is authoritative.

| ID | Rule |
| --- | --- |
| BR-01 | A raw-material batch contains between 1 and 100 bales. |
| BR-02 | `shipment_number` is globally unique. |
| BR-03 | `bale_number` is unique within a batch and may repeat across different batches. |
| BR-04 | The business identity of a bale is `shipment_number + bale_number`. |
| BR-05 | Business identifiers and material type are normalized per existing domain rules. |
| BR-06 | `received_at` represents only the business date of reception. |
| BR-07 | Every new bale is registered with status `in_warehouse`. |
| BR-08 | The only permitted states are `in_warehouse` and `delivered`. |
| BR-09 | The only permitted transition is `in_warehouse → delivered`. |
| BR-10 | A `delivered` bale cannot return to `in_warehouse` or be delivered again. |
| BR-11 | Delivery always affects the entire bale. |
| BR-12 | For this scope, `delivered` means delivered to and used by Production. |
| BR-13 | Net weight is `gross_weight_kg - container_weight_kg` and is never received as persistable client input. |
| BR-14 | Dtex and weights are handled as finite decimals; gross weight must exceed container weight. |
| BR-15 | Registration of the batch and all its bales is atomic. |
| BR-16 | Query filters combine via conjunction: a bale must satisfy all provided filters. |

## 6. API functional design

### 6.1 Endpoint catalog

| Capability | Method | Path | Primary result |
| --- | --- | --- | --- |
| Register batch | `POST` | `/api/v1/warehouse/bales` | Summary of the created batch |
| Query stock summary | `GET` | `/api/v1/warehouse/bales` | Aggregated counts and weights |
| Query bale detail | `GET` | `/api/v1/warehouse/bales/{shipment_number}/{bale_number}` | Single bale detail |
| Batch delivery | `POST` | `/api/v1/warehouse/bales/deliver` | Per-bale delivery results |

`GET /bales` without path parameters returns the stock summary (aggregated metrics). `GET /bales/{shipment_number}/{bale_number}` returns a single bale by its business identity. Neither returns an exhaustive listing.

The batch delivery endpoint accepts multiple bales from different batches in a single request. The individual PATCH is removed — a batch delivery with one element covers that case.

## 7. Batch registration

### 7.1 Endpoint

`POST /api/v1/warehouse/bales`

### 7.2 Request

| Field | Contract type | Required | Rule |
| --- | --- | ---: | --- |
| `shipment_number` | String | Yes | Non-empty, max 10 characters after normalization, globally unique |
| `received_at` | ISO date `YYYY-MM-DD` | Yes | Valid business date |
| `provider_name` | String | Yes | Non-empty after trimming |
| `bales` | Collection | Yes | Between 1 and 100 elements |
| `bales.n.bale_number` | String | Yes | Max 10 characters; unique within the batch |
| `bales.n.material_type` | String | Yes | Max 20 characters; normalized by domain |
| `bales.n.dtex` | Decimal string | Yes | Finite and greater than zero |
| `bales.n.gross_weight_kg` | Decimal string | Yes | Finite and greater than zero |
| `bales.n.container_weight_kg` | Decimal string | Yes | Finite, greater than zero, and less than gross weight |

No extra fields are accepted. Decimals continue to be sent as JSON strings to preserve precision.

### 7.3 Successful response

**Status:** `201 Created`

| Field | Type |
| --- | --- |
| `raw_material_batch_id` | UUID |
| `shipment_number` | Normalized string |
| `received_at` | ISO date |
| `provider_name` | String |
| `bale_count` | Integer |

The response does not include the `bales` array, net weight, or frontend temporary identifiers.

### 7.4 Required behavior

- Validate all input before persisting.
- Generate technical identities in the backend.
- Insert the batch first, then its bales within a single transaction.
- Roll back the entire operation on any error.
- Maintain stable translation of the `shipment_number` conflict.
- Produce indexed paths for errors associated with identifiable bales, e.g. `bales.17.gross_weight_kg`.

## 8. Aggregate stock summary

### 8.1 Endpoint

`GET /api/v1/warehouse/bales`

### 8.2 Filters

All filters are optional.

| Query parameter | Type | Semantics |
| --- | --- | --- |
| `received_from` | ISO date | Inclusive lower bound on reception date |
| `received_to` | ISO date | Inclusive upper bound on reception date |
| `shipment_number` | String | Exact match after normalization |
| `status` | Enum | `in_warehouse` or `delivered` |
| `provider_name` | String | Case-insensitive exact match after trimming |
| `material_type` | String | Exact match after normalization |
| `dtex` | Decimal string | Exact decimal match |

Date bounds are inclusive. If both are provided, `received_from` must not be later than `received_to`.

### 8.3 Successful response

**Status:** `200 OK`

| Field | Type | Definition |
| --- | --- | --- |
| `total_bale_count` | Integer | Bales matching the filters |
| `in_warehouse_bale_count` | Integer | Filtered bales currently in warehouse |
| `delivered_bale_count` | Integer | Filtered bales delivered/used |
| `net_weight_total_kg` | Decimal string | Total filtered net weight |
| `net_weight_in_warehouse_kg` | Decimal string | Filtered net weight in warehouse |
| `net_weight_delivered_kg` | Decimal string | Filtered net weight delivered/used |

When no matches exist, counts must be `0` and weights must be serialized as zero decimals; the response is not `404`.

When a status filter is applied, the total represents only that subset and the counter for the other status is zero. Weights must be computed in PostgreSQL on persisted data; the backend must not load all bales to aggregate them in memory.

## 9. Individual bale query

### 9.1 Endpoint

`GET /api/v1/warehouse/bales/{shipment_number}/{bale_number}`

The path uses the business identity directly. Both values are normalized before lookup. This avoids exposing internal UUIDs to the operator, who identifies bales by the labels on physical bales.

### 9.2 Path parameters

| Parameter | Type | Rule |
| --- | --- | --- |
| `shipment_number` | String | Normalized batch identifier |
| `bale_number` | String | Normalized bale identifier within that batch |

### 9.3 Successful response

**Status:** `200 OK`

| Field | Type |
| --- | --- |
| `id` | UUID |
| `shipment_number` | String |
| `bale_number` | String |
| `received_at` | ISO date |
| `provider_name` | String |
| `material_type` | String |
| `dtex` | Decimal string |
| `gross_weight_kg` | Decimal string |
| `container_weight_kg` | Decimal string |
| `net_weight_kg` | Computed decimal string |
| `status` | `in_warehouse` or `delivered` |
| `delivery_date` | ISO date or `null` |

### 9.4 Not found

When the composite identity does not exist, the backend responds `404 Not Found` with code `bale_not_found`. It must not reveal whether the batch existed but the bale did not, because both values form a single lookup identity for the consumer.

## 10. Batch delivery

### 10.1 Endpoint

`POST /api/v1/warehouse/bales/deliver`

This is the primary delivery interface for the frontend checklist workflow. The operator prepares a list of bales read from physical labels and submits them in a single request with a shared delivery date.

### 10.2 Request

| Field | Type | Required | Rule |
| --- | --- | ---: | --- |
| `delivery_date` | ISO date `YYYY-MM-DD` | Yes | Business date when the physical delivery occurred |
| `bales` | Collection | Yes | Between 1 and 50 elements |
| `bales.n.shipment_number` | String | Yes | Batch identifier; normalized before lookup |
| `bales.n.bale_number` | String | Yes | Bale identifier within batch; normalized before lookup |

No extra fields are accepted. The endpoint uses the business identity (not UUID) because the operator reads these values from physical labels.

Duplicates within the same request (same `shipment_number + bale_number` after normalization) must be rejected with `422 duplicate_delivery_identity`.

### 10.3 Successful response

**Status:** `200 OK` (all delivered) or `207 Multi-Status` (partial results)

```json
{
  "delivery_date": "2026-07-28",
  "delivered_count": 2,
  "failed_count": 1,
  "results": [
    {
      "shipment_number": "PART-001",
      "bale_number": "F-01",
      "status": "delivered",
      "error": null
    },
    {
      "shipment_number": "PART-001",
      "bale_number": "F-02",
      "status": "already_delivered",
      "error": { "code": "bale_already_delivered", "message": "Bale was already delivered." }
    },
    {
      "shipment_number": "PART-003",
      "bale_number": "F-99",
      "status": "not_found",
      "error": { "code": "bale_not_found", "message": "Bale identity does not exist." }
    }
  ]
}
```

### 10.4 Per-bale result statuses

| Status | Meaning |
| --- | --- |
| `delivered` | Successfully transitioned to delivered in this request |
| `already_delivered` | Bale exists but was already delivered (no change made) |
| `not_found` | Business identity does not exist in the system |

### 10.5 Response status code logic

- `200 OK` — All bales in the request were successfully delivered.
- `207 Multi-Status` — At least one bale failed (not_found or already_delivered) while others succeeded or all failed.
- `422` — Request-level validation failure (empty collection, invalid date, duplicate identities). No bales are processed.

### 10.6 Required behavior

- Validate the request structure before processing any bale.
- Reject duplicate identities within the same request (after normalization).
- For each bale in order:
  1. Resolve the business identity (`shipment_number + bale_number`) to the internal record.
  2. If not found → record `not_found` result, continue to next bale.
  3. If already `delivered` → record `already_delivered` result, continue to next bale.
  4. Execute `bale.deliver(delivery_date)` via the domain rule.
  5. Record `delivered` result.
- Persist all successful transitions. Failed bales do not block successful ones.
- A bale that succeeds within this request must not be rolled back due to a later bale failing.
- Concurrency: if two requests overlap on the same bale, exactly one succeeds; the other receives `already_delivered` for that bale.

### 10.7 Atomicity model

This endpoint uses **best-effort with per-bale reporting** (not all-or-nothing):

- Each bale is processed independently.
- A failure in bale N does not prevent bale N+1 from being processed.
- Successfully delivered bales are committed regardless of other failures.
- The frontend uses the per-bale results to show which deliveries succeeded and which need attention.

This matches the operational reality: the physical delivery already happened. The system records facts; a conflict on one bale does not undo the physical delivery of another.

### 10.8 Limits

- Maximum 50 bales per request (operational safeguard, not a business limit).
- No minimum other than 1.

## 11. Error contract

All operations maintain the current envelope:

| Field | Usage |
| --- | --- |
| `error.code` | Stable, client-processable code |
| `error.message` | Human-readable cause summary |
| `error.fields` | Errors associated with concrete paths; empty collection when not applicable |

### 11.1 Minimum matrix

| Status | Code | Case |
| ---: | --- | --- |
| 404 | `bale_not_found` | Requested bale does not exist (detail query) |
| 409 | `duplicate_shipment_number` | Batch already registered |
| 422 | `request_validation_error` | Type, required field, value, or filter invalid |
| 422 | `duplicate_bale_number` | Bale number repeated within a registration batch |
| 422 | `duplicate_delivery_identity` | Same bale identity repeated within a delivery request |
| 422 | `domain_validation_error` | Domain invariant violated |
| 500 | `internal_server_error` | Unexpected failure without internal details |

Note: per-bale delivery failures (`already_delivered`, `not_found`) are reported within the `207` response body, not as top-level HTTP error codes.

### 11.2 Field paths

- Pydantic errors must preserve concrete paths such as `received_at`, `status`, or `bales.17.dtex`.
- General batch errors may point to `shipment_number`.
- When the backend knows the index of the invalid bale, it must avoid generic paths like `bales[].field`.
- Internal database messages, traces, SQL, and secrets are never included in responses.

## 12. Application architecture

### 12.1 Principles

- The capability remains under `warehouse.bales`.
- HTTP models do not enter the domain or ports.
- SQLAlchemy remains restricted to persistence adapters and infrastructure.
- Writes use domain entities and rules.
- Queries return read projections specific to each use case.
- No event sourcing, command bus, or separate read database is introduced.

### 12.2 Required use cases

| Type | Responsibility |
| --- | --- |
| Command | Register a complete raw-material batch |
| Query | Get aggregate stock summary with filters |
| Query | Get bale detail by business identity |
| Command | Deliver multiple bales in a batch (best-effort, per-bale results) |

The delivery use case must reuse `Bale.deliver()`. It must not directly modify the status string in the router or repository.

### 12.3 Ports and adapters

The design must incorporate:

- A read port for the aggregate stock summary.
- A read port for bale detail by `shipment_number + bale_number`.
- Bale repository capability to resolve a business identity to a bale record.
- Capability to persist the updated state with concurrency control.
- SQLAlchemy adapters implementing queries and modifications.
- Differentiated dependency providers per use case, avoiding coupling a single provider only to registration.

Queries may read directly from projections built with joins and aggregates. They do not need to reconstruct `RawMaterialBatch` or full `Bale` aggregates when no domain behavior is executed.

### 12.4 Domain model contracts

The domain layer must expose the following contracts, independent of FastAPI, Pydantic, and SQLAlchemy:

**ReceptionDate** — Business date value object:

- Accepts only `datetime.date` (calendar date).
- Rejects `datetime.datetime` and timezone-aware values.
- Does not convert to UTC or invent a time component.
- Used by the registration command and persisted as `DATE`.

**DeliveryDate** — Business date value object:

- Accepts only a valid calendar date.
- Rejects datetime and timezone values.
- Required by the delivery transition; cannot be null when status is `delivered`.
- Independent of HTTP framework concerns.

**Bale entity** — State and transition:

```python
class Bale:
    status: BaleStatus          # in_warehouse | delivered
    delivery_date: DeliveryDate | None

    def deliver(self, delivery_date: DeliveryDate) -> None:
        """Irreversible transition. Raises on second call."""
```

Invariants:

- `status = in_warehouse` implies `delivery_date is None`.
- `status = delivered` implies `delivery_date is not None`.
- A second `deliver()` call raises a transition error.
- `delivery_date` is set atomically with the status change.

## 13. Persistence and migrations

### 13.1 Business date

- Column `raw_material_batches.received_at` must change from `timestamp with time zone` to `DATE`.
- The SQLAlchemy record must use a date type.
- The domain must replace `ReceptionDateTime` semantics with a business date value.
- Commands, results, mappers, requests, responses, and tests must use the same type.
- The migration must explicitly define how to preserve the business date of any pre-existing data and validate the result before removing temporal semantics.
- Technical audit date, if required in the future, will be a separate field such as `created_at`; it is not part of this scope.

### 13.2 Delivery date column

The `raw_material_bales` table must include:

```sql
delivery_date DATE NULL
```

A named CHECK constraint must enforce the state-date invariant:

```sql
CONSTRAINT ck_raw_material_bales_status_delivery_date CHECK (
    (status = 'in_warehouse' AND delivery_date IS NULL)
    OR
    (status = 'delivered' AND delivery_date IS NOT NULL)
)
```

The existing `ck_raw_material_bales_status` constraint (allowed values) is preserved alongside this new constraint.

### 13.3 Indexes

In addition to the current uniqueness and index constraints, indexes must be evaluated and verified for:

- Batch reception date.
- Bale status.
- Material type.
- Combined queries by shipment number and bale number, partially covered by existing constraints.

Final selection must be justified with actual query plans from `summary` and `detail`. Indexes must not be created for filters that are not part of the approved contract.

### 13.4 Integrity

- Named primary key, foreign key, uniqueness, and status constraints are preserved.
- The new migration must maintain RLS enabled and the current privilege policy.
- Access policies are not added while authentication and authorization remain out of scope.
- Weights and dtex remain in `NUMERIC` columns.

## 14. Concurrency and transactions

- Batch registration preserves a single transaction for batch and bales.
- Batch delivery processes each bale independently; a failure on one bale does not roll back others.
- Delivery must apply row locking or equivalent conditional update to ensure the expected state is `in_warehouse`.
- A concurrent conflict produces `already_delivered` in the per-bale result.
- Queries must not perform commits or modify entities.
- Any exception during a write must trigger rollback for the affected bale.

## 15. Security and integration

### 15.1 CORS

The application must allow calls from the frontend via a configurable list of origins:

- Origins are obtained from typed environment configuration.
- Local development allows only the origins declared for Vite.
- Production does not use wildcard.
- Credentials and `DATABASE_URL` are not exposed to the browser.
- Invalid or missing CORS configuration must cause the application to fail at startup, not silently allow all origins.

### 15.2 Data security

- Strict validation and prohibition of extra fields are preserved.
- Generic responses are maintained for unexpected errors.
- Logs may contain technical context but not secrets or complete sensitive payloads.
- RLS and existing privileges must not be weakened to facilitate development.

## 16. Non-functional requirements

| ID | Requirement |
| --- | --- |
| NFR-01 | Operations must preserve end-to-end decimal accuracy. |
| NFR-02 | Stock summary must be resolved via SQL aggregation without materializing all bales in memory. |
| NFR-03 | POST must support 100 bales within normal service operational limits. |
| NFR-04 | The API must maintain deterministic contracts documented in OpenAPI. |
| NFR-05 | No `500` error may expose exceptions, SQL, internal paths, or secrets. |
| NFR-06 | Writes must be atomic and concurrency-safe. |
| NFR-07 | Queries must leverage indexes compatible with their filters and joins. |
| NFR-08 | Changes must not introduce framework dependencies in domain or application. |
| NFR-09 | Configuration must fail early when a required value is invalid. |
| NFR-10 | The solution must preserve Python 3.13, `uv`, `unittest`, FastAPI, SQLAlchemy, Psycopg, and Supabase migrations as already adopted. |

## 17. Testing strategy

### 17.1 Domain

- Valid and invalid business date.
- Successful transition to `delivered`.
- Rejection of a second delivery.
- Preservation of identifier, dtex, and weight rules.

### 17.2 Application

- Registration of 1 and 100 bales.
- Rejection of 0 and more than 100 bales.
- Summary result without bale collection.
- Correct filter construction.
- Detail found and not found.
- Batch delivery: all succeed, partial success, all not found, all already delivered.
- Batch delivery: duplicate identity rejection.
- Single-bale delivery: successful, non-existent, and already-delivered.
- Rollback and conflict translation.

### 17.3 Unit persistence

- Date mapping.
- Detail projection with join.
- Aggregates and zeros when no matches exist.
- Filter combination.
- Bale loading and update.

### 17.4 API and OpenAPI

- Methods, paths, parameters, status codes, and models.
- ISO date without time component.
- Decimals serialized as strings.
- POST response without `bales`.
- Indexed field error paths.
- Rejection of extra fields and disallowed states.
- CORS for allowed origin and rejection of unauthorized origin.

### 17.5 PostgreSQL integration

- Migration of `received_at` to `DATE`.
- Date and decimal round-trips.
- Atomic registration of 100 bales.
- Correct summary with each filter and representative combinations.
- Query by composite identity.
- Expected query plans and indexes.
- Concurrent transition: one successful request and one conflict.
- State persistence after commit.
- Rollback on failures.

Unit tests with test doubles may continue as support but do not substitute verifications of types, constraints, concurrency, diagnostics, and real aggregations in PostgreSQL.

## 18. Acceptance criteria

> For authoritative business rules, see the [normative PRD](../../../docs/prd/warehouse/bale-management.md).
> The acceptance criteria below are implementation-level verification points derived from the PRD.

| ID | Criterion |
| --- | --- |
| AC-01 | POST accepts `received_at` as `YYYY-MM-DD` and rejects values with time. |
| AC-02 | The persisted reception column is `DATE`. |
| AC-03 | POST accepts between 1 and 100 bales and rejects collections outside that range. |
| AC-04 | The `201` response contains only the five approved summary fields. |
| AC-05 | A duplicate `shipment_number` produces `409 duplicate_shipment_number`. |
| AC-06 | Identifiable bale errors include an indexed path compatible with the grid. |
| AC-07 | The stock summary endpoint applies all optional filters conjunctively. |
| AC-08 | Stock summary returns correct counts and weights computed by PostgreSQL. |
| AC-09 | A stock summary with no matches returns zeros and status `200`. |
| AC-10 | Detail requires `shipment_number` and `bale_number`. |
| AC-11 | Detail returns the UUID, header, attributes, net weight, status, and delivery date. |
| AC-12 | A non-existent business identity produces `404 bale_not_found`. |
| AC-13 | Batch delivery accepts 1–50 bales identified by business identity. |
| AC-14 | Batch delivery returns per-bale results with `delivered`, `already_delivered`, or `not_found`. |
| AC-15 | Batch delivery uses `200` for all-success and `207` for partial results. |
| AC-16 | A successful bale in a batch is not rolled back due to another bale failing. |
| AC-17 | Two concurrent deliveries of the same bale cannot both succeed. |
| AC-18 | Duplicate identities within a batch delivery request produce `422`. |
| AC-19 | All paths and responses are correctly represented in OpenAPI. |
| AC-20 | The frontend can consume the API from an explicitly configured CORS origin. |
| AC-21 | Unit and PostgreSQL integration suites pass without failures. |
| AC-22 | Repository documentation remains aligned with the implementation. |

## 19. Recommended implementation sequence

1. Align business date, 100-bale limit, and summary response for registration.
2. Incorporate the date migration and initial indexes.
3. Implement the individual bale query by business identity path parameters.
4. Implement the batch delivery endpoint with per-bale resolution and results.
5. Implement the aggregate stock summary and its filters.
6. Extend composition, HTTP contracts, errors, and OpenAPI.
7. Configure CORS.
8. Complete PostgreSQL tests and validate integration with the frontend.

Each block must keep the registration endpoint functional and maintain alignment across domain, application, adapters, migrations, OpenAPI, and tests.

## 20. Implementation risks and pending decisions

| Risk | Treatment |
| --- | --- |
| Conversion of existing timestamps to date | Define and test an explicit date-preservation rule before executing the migration |
| Concurrent double delivery | Row lock or conditional update with expected state |
| Null summations | Normalize aggregates without results to zero decimal |
| Filters degrading performance | Verify real plans and add only justified indexes |
| Domain errors without bale index | Preserve the index during construction/validation to produce a useful path |
| ORM and migration divergence | Maintain schema contract tests in PostgreSQL |
| Permissive CORS | Use explicit per-environment list and prohibit wildcard in production |

## 21. Definition of done

The capability is considered done when:

- All four endpoints meet the contracts of this technical specification.
- Registration uses simple dates, limits the collection, and returns a summary.
- Stock summary, individual bale query, and batch delivery can integrate without simulated data.
- The irreversible transition is correct even under concurrency.
- Batch delivery reports per-bale results without rolling back successful bales.
- Migrations, records, mappers, and domain use consistent types.
- Errors allow the frontend to differentiate request-level failures from per-bale results.
- OpenAPI reflects actual behavior.
- Unit and PostgreSQL tests cover the acceptance criteria.
- CORS configuration permits authorized integration with the frontend.
- Repository documentation preserves no descriptions incompatible with the implementation.
