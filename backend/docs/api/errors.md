---
document_type: technical-spec
status: active
implementation: partial
scope: backend/api
authority: explanatory
owner: backend
last_reviewed: 2026-07-27
---

# Error Contract

Standard error response format for the Colibri Hub backend API.

---

## 1. Error Response Structure

All error responses use a consistent envelope:

```json
{
  "error": {
    "code": "duplicate_shipment_number",
    "message": "A batch with this shipment number already exists.",
    "fields": []
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `error.code` | string | Stable, machine-readable error identifier |
| `error.message` | string | Human-readable summary of the failure |
| `error.fields` | array | Field-level errors with path and detail; empty when not applicable |

## 2. Field-Level Errors

When validation fails on specific fields, the `fields` array provides indexed
paths compatible with frontend form/grid rendering:

```json
{
  "error": {
    "code": "request_validation_error",
    "message": "Validation failed.",
    "fields": [
      { "path": "bales.3.gross_weight_kg", "message": "Must be greater than zero." },
      { "path": "received_at", "message": "Invalid date format." }
    ]
  }
}
```

Field paths use dot notation with zero-based indexes for collection items
(e.g., `bales.17.dtex`).

## 3. HTTP Status Codes

### 201 Created

Returned on successful resource creation (`POST`). No error body.

### 400 Bad Request

Malformed JSON that cannot be parsed.

### 404 Not Found

| Code | Scenario |
|------|----------|
| `bale_not_found` | The requested bale does not exist |

The response does not reveal whether the shipment exists but the bale does not —
the compound identity is treated as a single lookup key.

### 409 Conflict

Uniqueness violations and invalid state transitions:

| Code | Scenario |
|------|----------|
| `duplicate_shipment_number` | A batch with this shipment number already exists |
| `bale_already_delivered` | The bale has already been transitioned to `delivered` |

Only the two named uniqueness constraints (`uq_raw_material_batches_shipment_number`,
`uq_raw_material_bales_raw_material_batch_bale_number`) are translated to
application-level conflicts. Unknown integrity failures propagate as 500.

### 422 Unprocessable Entity

Validation errors — request is well-formed JSON but violates schema or domain
rules:

| Code | Scenario |
|------|----------|
| `request_validation_error` | Pydantic validation failure (type, required field, value constraint) |
| `duplicate_bale_number` | Bale number repeated within the same batch |
| `domain_validation_error` | Domain invariant violated (e.g., gross weight ≤ tare) |

### 500 Internal Server Error

| Code | Scenario |
|------|----------|
| `internal_server_error` | Unexpected failure; no internal details exposed |

Internal exceptions, SQL, stack traces, and secrets are never included in error
responses. They are logged server-side only.

## 4. Design Principles

- **Stability:** Error codes are stable identifiers that clients can match on.
- **Specificity:** Field paths allow frontends to associate errors with inputs.
- **Security:** Internal state is never leaked to the client.
- **Consistency:** All endpoints use the same envelope regardless of HTTP status.
