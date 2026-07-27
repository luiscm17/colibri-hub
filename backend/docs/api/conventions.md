---
document_type: technical-spec
status: active
implementation: partial
scope: backend/api
authority: explanatory
owner: backend
last_reviewed: 2026-07-27
---

# API Conventions

HTTP API conventions for the Colibri Hub backend.

---

## 1. Base Path

All endpoints are served under:

```
/api/v1/
```

## 2. Routing Structure

Routes follow a context-based capability pattern:

```
/api/v1/{context}/{capability}
```

| Segment | Meaning | Example |
|---------|---------|---------|
| `context` | Business bounded context | `warehouse` |
| `capability` | Specific resource or operation | `bales`, `bales/summary` |

Current routes:

| Method | Path | Capability |
|--------|------|------------|
| `POST` | `/api/v1/warehouse/bales` | Register a raw-material batch |
| `GET` | `/api/v1/warehouse/bales/summary` | Inventory summary with filters |
| `GET` | `/api/v1/warehouse/bales/detail` | Single bale lookup |
| `PATCH` | `/api/v1/warehouse/bales/{bale_id}/status` | Bale state transition |

## 3. Request and Response Format

- **Content type:** `application/json`
- **Validation:** Pydantic models with strict field enforcement
- **Extra fields:** Rejected — no unknown fields accepted
- **Decimals:** Serialized as JSON strings to preserve precision
- **Dates:** ISO 8601 format (`YYYY-MM-DD` for business dates)
- **Identifiers:** UUIDs generated server-side

## 4. HTTP Methods

| Method | Semantics |
|--------|-----------|
| `POST` | Create a new resource (batch registration) |
| `GET` | Read resource or computed projection (summary, detail) |
| `PATCH` | Partial update of a specific field (state transition) |

`PUT` and `DELETE` are not used in the current API surface.

## 5. Status Codes

| Code | Usage |
|------|-------|
| `200` | Successful read or update |
| `201` | Resource created successfully |
| `400` | Malformed request (unparseable JSON) |
| `404` | Resource not found |
| `409` | Conflict (uniqueness violation, invalid state transition) |
| `422` | Validation error (field-level or domain rule) |
| `500` | Unexpected internal error |

## 6. Versioning Strategy

- Version is embedded in the URL path (`/api/v1/`)
- Breaking changes require a new version prefix
- Non-breaking additions (new optional fields, new endpoints) do not increment
  the version

## 7. Query Parameters

- Filters on `GET` endpoints use query parameters
- All filters are optional unless documented otherwise
- Multiple filters combine conjunctively (AND)
- String filters apply exact match after normalization
- Date filters are inclusive on both bounds

## 8. Response Envelope

Successful responses return the resource or projection directly (no wrapper).
Error responses use the standard error contract defined in
[errors.md](errors.md).
