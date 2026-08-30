---
document_type: technical-spec
status: active
scope: yarn-spinning
authority: explanatory
owner: backend
last_reviewed: 2026-08-29
replaces: null
---

# Backend Yarn Spinning

Yarn Spinning provides the public backend contract for recording, consulting, and correcting production discharges, skeining production, progress, process quality, and waste. It enforces authoritative operational rules and returns calculated values; clients may validate presentation but do not decide business outcomes.

## Purpose, Boundary, and Authorities

Yarn Spinning owns operational records, their continuity and reconciliation outcomes, correction evidence, and section and consolidated operational read projections. Its productive sections are Preparation, Ring Spinning, Bobbin Winding, Twisting, and Skeining.

It also owns Process Quality measurement profiles and their effective versions. A profile is
configuration, not a capture record or generic Shared Reference Data; it may reference shared units,
sections, machines, yarn counts, and employees. Access Control authorizes profile management,
activation, capture, and correction but does not own physical parameters, units, methods,
calculations, or tolerances.

It does not own Warehouse custody, physical lot assembly, lot-stage history, final lot quality, finished-product handoff, authorization policy, or shared-reference administration. Skeining records have no lot attribution and create no availability, allocation, reservation, consumption, or double-use-prevention rule.

1. The [Yarn Spinning PRD](../../../docs/prd/operation/yarn-spinning.md) is the closed business authority for record semantics, calculations, validation, correction policy, and acceptance criteria.
2. The [Access Control PRD](../../../docs/prd/access-control.md) and [Backend Access Control](access-control.md) govern authorization actions, scopes, and evaluation.
3. [API Conventions](../api/conventions.md) and [Error Contract](../api/errors.md) govern HTTP, identifiers, decimals, pagination conventions, and the shared error envelope.
4. This specification owns the public Yarn Spinning wire contract. It does not define storage, migrations, internal source organization, or authorization policy.

## Contract-Wide Conventions

All routes use `/api/v1`, JSON, strict request validation, server-generated stable UUID identifiers, ISO 8601 timestamps, and the shared error envelope. Business dates are `YYYY-MM-DD`. Decimal measurements and calculated quantities are JSON strings in their stated units; counts are JSON integers. Successful responses are direct resources or projections, never wrapper envelopes.

The server derives authenticated identity, authorization scope, calculated values, capture timestamps, correction evidence, and all current-state outcomes. `supervisor_user_id` is an explicit header value for section-production capture. `foreman_user_id` is never client input: it is derived from the authenticated session and returned in authorized record representations where foreman / recorder attribution applies.

## Public API

| Operation | Method | Path |
| --- | --- | --- |
| Capture section production | `POST` | `/api/v1/spinning/sections/{section}/production` |
| Discover / list Quality profiles | `GET` | `/api/v1/spinning/process-quality/profiles` |
| Create Quality profile | `POST` | `/api/v1/spinning/process-quality/profiles` |
| List / create profile versions | `GET` / `POST` | `/api/v1/spinning/process-quality/profiles/{profile_id}/versions` |
| Read / change profile-version lifecycle | `GET` / `PATCH` | `/api/v1/spinning/process-quality/profiles/{profile_id}/versions/{profile_version}` |
| Capture process quality | `POST` | `/api/v1/spinning/process-quality` |
| Capture waste | `POST` | `/api/v1/spinning/waste` |
| Read records / detail | `GET` | `/api/v1/spinning/records` / `/api/v1/spinning/records/{family}/{record_id}` |
| Read correction history | `GET` | `/api/v1/spinning/records/{family}/{record_id}/corrections` |
| Read section metrics | `GET` | `/api/v1/spinning/sections/{section}/metrics` |
| Read consolidated metrics | `GET` | `/api/v1/spinning/consolidated/metrics` |
| Prepare Progress prefill | `GET` | `/api/v1/spinning/sections/{section}/progress-preparation?business_date=…&shift_code=…&machine_id=…&yarn_count_id=…` |
| Correct a record | `PATCH` | `/api/v1/spinning/{family}/{record_id}` |

### Process Quality Profiles

`GET /api/v1/spinning/process-quality/profiles` discovers active versions available for a new
capture. It requires `section_id`; `machine_id` and `yarn_count_id` are optional. The server applies
the existing Process Quality authorization and returns only active, applicable versions. Profile
administration uses the same Process Quality scope and existing Access actions; it introduces no new
Access action or scope.

```json
{
  "items": [{
    "profile_id": "7c4f8c3f-4d3d-4f92-a4db-e0c9831db8cf",
    "profile_version": 3,
    "version": 3,
    "name": "Preparation sliver sample",
    "lifecycle_state": "active",
    "applicability": {"section_id": "preparation", "machine_ids": [], "yarn_count_ids": []},
    "capture_mode": "sample",
    "sample_count": 10,
    "parameters": [{"key": "sliver_weight", "label": "Sliver weight", "unit": "g", "ordered": true}],
    "results": [
      {"key": "x_average", "label": "Average", "unit": "g", "operation_key": "sample_average"},
      {"key": "x_percentage_error", "label": "Relative standard error", "unit": "%", "operation_key": "relative_standard_error_percent"}
    ],
    "tolerance_rules": [{"result_key": "x_percentage_error", "minimum": "0", "maximum": "5"}],
    "approved_calculation_operation_keys": ["sample_average", "relative_standard_error_percent"]
  }]
}
```

`machine_ids` and `yarn_count_ids` are empty only when that restriction does not apply.
`sample_count` is required for `capture_mode: "sample"`, is an integer from 10 through 15, and is
omitted for `machine_register` and `random`. Every parameter definition has `key`, `label`, `unit`,
and `ordered`; only Sample parameters may be ordered. Every result definition has `key`, `label`,
`unit`, and one selected `operation_key`. Every tolerance rule has `result_key` and optional
decimal-string `minimum` and `maximum`, with at least one bound. Parameter and result keys are stable
within a profile identity. `profile_version` identifies the immutable definition sequence; `version`
is its integer optimistic-concurrency token and is independent of `profile_version`. Arbitrary
formulas or expressions are never accepted.

`POST /api/v1/spinning/process-quality/profiles` accepts `name`, `applicability`, `capture_mode`, `sample_count` when applicable,
`parameters`, `results`, `tolerance_rules`, and `approved_calculation_operation_keys`; it creates
profile version `1` in `inactive` lifecycle state and returns that definition with `201`. `POST
/api/v1/spinning/process-quality/profiles/{profile_id}/versions` accepts the same definition plus integer `expected_version` and
creates the next inactive version with `201`; it never modifies an existing definition. `GET
/api/v1/spinning/process-quality/profiles/{profile_id}/versions` returns all authorized versions, including retired versions, and
`GET /api/v1/spinning/process-quality/profiles/{profile_id}/versions/{profile_version}` returns one authorized definition. `PATCH
/api/v1/spinning/process-quality/profiles/{profile_id}/versions/{profile_version}` accepts exactly
`{"lifecycle_state":"active"|"retired","expected_version":3}` and returns that version with an
incremented `version`. Retirement prevents new capture but preserves historical reads.

### Progress Continuity Preparation

`GET /api/v1/spinning/sections/{section}/progress-preparation?business_date=…&shift_code=…&machine_id=…&yarn_count_id=…`
prepares automatic visible Progress prefill only for Progress-applicable sections. `{section}` derives
the applicable section read scope. `business_date`, `shift_code`, `machine_id`, and `yarn_count_id`
are all required query parameters and identify the requested capture context. The server validates
section applicability and the selected identities' catalog and capture-context membership, including
that the machine belongs to the addressed section.

The server resolves the immediately preceding logical Progress record from current corrected state,
using A → B → C → next-business-day A for the same section, machine, and yarn-count identity. It
returns the configuration identity, derived input weight, whether that input has a predecessor origin
or is absent, and the predecessor's operative spindle count and worked hours as current-editable
suggestions. A changed or new yarn-count identity is a new stream: when it has no predecessor, the
server returns derived input zero. The operation is read-only and nonpersistent, returns only
authorized configuration and derived suggestions, and grants no authorization.

It does not prepare or copy Production Discharge events, weights, samples, Process Quality, Waste,
Skeining, calculated values, or dashboard data. It is neither a persisted event nor a version,
correction, or client-supplied input override.

### Capture Section Production

`{section}` selects the section. It is not repeated in the request body, and the server derives the authorization scope from the addressed section resource. The body includes only applicable record-family arrays; inapplicable families are omitted, not sent as empty placeholders. A successful capture is atomic across every included family.

```json
{
  "business_date": "2026-05-13",
  "shift_code": "A",
  "supervisor_user_id": "emp_rogelio",
  "discharges": [
    {
      "machine_id": "machine_ring_01",
      "yarn_count_id": "453254",
      "gross_weight_kg": "82.440",
      "spindle_tare_weight_g": "40.0",
      "operative_spindle_count": 200,
      "cart_weight_kg": "9.000",
      "roving_count": 8,
      "observations": null
    }
  ],
  "progress": [
    {
      "machine_id": "machine_ring_01",
      "yarn_count_id": "453254",
      "sample_gross_weight_g": "124.5",
      "sample_tare_weight_g": "4.5",
      "operative_spindle_count": 200,
      "worked_hours": "8.0",
      "reconciliation_note": null
    }
  ]
}
```

`discharges` items are distinct, repeatable Production Discharge events. They are not keyed by
machine, business date, shift, yarn count, or material type, whether separately or together. A
response exposes a stable `record_id` for each persisted discharge event, including multiple events
with the same apparent dimensions.

| Family | Request contract | Server-owned response values |
| --- | --- | --- |
| Production discharge | The shown fields; `roving_count` and `observations` are optional. `net_weight_kg` is not accepted. | `record_id`, integer `version`, `net_weight_kg`, `captured_at`, and `foreman_user_id` attribution. The associated material type is resolved from the referenced yarn count where applicable. |
| Progress | `machine_id`, `yarn_count_id`, conditional `sample_gross_weight_g`, `sample_tare_weight_g`, and `operative_spindle_count`; optional `worked_hours` and reconciliation note. | `record_id`, integer `version`, `input_weight_kg`, `discharged_weight_kg`, `output_weight_kg`, net process production, and `captured_at`. |

Progress is unique by section + machine + business date + shift + yarn count: one existing Progress
record occupies that identity. This is distinct from repeatable Production Discharge events. For
Progress, `input_weight_kg` is derived from the immediately preceding logical Progress output in the
A → B → C → next-business-day A sequence for the same section, machine, and yarn-count identity, or
is zero when no predecessor exists. `discharged_weight_kg` is derived from authoritative discharge
net weights for that machine and shift, or is zero when none exist. `output_weight_kg` is the sole
closing in-machine quantity and, where spindle sampling applies, is derived from the conditional
sample inputs and operative spindle count. Clients never submit `input_weight_kg`,
`discharged_weight_kg`, or `output_weight_kg`.

### Capture Process Quality, Skeining, and Waste

Process Quality and Waste are independent transversal captures. Skeining creation remains in the
established atomic section-production route, `POST /api/v1/spinning/sections/skeining/production`;
there is no second Skeining creation endpoint.

Process Quality accepts exactly the following profile-bound raw capture envelope:

```json
{
  "profile_id": "7c4f8c3f-4d3d-4f92-a4db-e0c9831db8cf",
  "profile_version": 3,
  "section_id": "preparation",
  "business_date": "2026-05-13",
  "shift_code": "A",
  "inspector_user_id": "a9ddf3da-f1c7-4875-8ce8-0c0d5a6f0a6d",
  "parameters": [{"key": "sliver_weight", "values": ["4.20", "4.10", "4.30", "4.20", "4.10", "4.20", "4.30", "4.20", "4.10", "4.20"]}],
  "observations": null
}
```

`machine_id` and `yarn_count_id` are required only when the selected profile requires them; otherwise
they are omitted. `parameters` contains exactly the profile-defined keys. Each entry contains only
`key` and decimal-string `values`; ordered Sample values have exactly the configured `sample_count`.
Machine Register and Random cardinality is defined by their selected profile. Requests reject
`results`, tolerance outcomes, units, calculated values, operation keys, and expressions.

Its `201` response contains `record_id`, `family: "process_quality"`, `version`, `profile_id`,
`profile_version`, all capture-context members, retained `parameters`, `results`,
`tolerance_outcome`, `tolerance_evaluations`, `observations`, `captured_at`, and `foreman_user_id`.
Each result is `{"key":"…","value":"…"|null,"unit":"…","availability":"available"|"unavailable"}`.
Each tolerance evaluation is `{"result_key":"…","minimum":"…"|null,"maximum":"…"|null,"outcome":"within_tolerance"|"outside_tolerance"|"unavailable"}`. Preparation returns
`x_average` and `x_percentage_error` only when the applied profile defines those result keys; they
are not global Quality fields. A zero average makes the latter unavailable, never a fabricated number.

For the Skeining section route, the applicable `skeining` array contains:

```json
{"machine_id":"machine_skeining_01","yarn_count_id":"453254","skein_count":120,"estimated_unit_weight_g":"35.0","operator_name":"Example operator","observations":null}
```

Each created Skeining record returns those values plus `record_id`, `family: "skeining"`, `version`,
the header `business_date`, `shift_code`, and `supervisor_user_id`, server-derived
`foreman_user_id`, `captured_at`, and calculated `estimated_total_weight_kg`. It accepts no
material-type, lot, spindle, tare, cart, or direct total-weight member.

Waste accepts and returns:

```json
{"section_id":"ring_spinning","machine_group_id":"ring_group_1","business_date":"2026-05-13","shift_code":"A","waste_weight_kg":"2.500","observations":null}
```

The `201` response adds `record_id`, `family: "waste"`, `version`, `captured_at`, and
`foreman_user_id`. It accepts no individual-machine, material-type, lot, or theoretical-waste member.
Out-of-specification skeins are reprocessing material and cannot be Waste.

### Record Reads, History, and Metrics

`GET /api/v1/spinning/records` returns authorized current-state records. Optional filters are
`family` (`production_discharge`, `progress`, `process_quality`, `skeining`, or `waste`), `section_id`,
`machine_id`, `machine_group_id`, `yarn_count_id`, `shift_code`, `business_date_from`, and
`business_date_to`. Filters combine with AND semantics, strings use exact-match normalization, and
date bounds are inclusive.

Only this operational record list is cursor-paginated. It accepts an opaque `cursor` and `limit`,
which defaults to `50` and must be an integer from `1` through `100`. Its fixed stable order is
business date descending, logical shift descending, captured timestamp descending, then `record_id`
descending. A cursor continues that exact ordered result set and is opaque to clients. Its successful
response is exactly:

```json
{
  "items": ["authorized current record representations"],
  "next_cursor": "opaque cursor or null"
}
```

The list never returns `total`. Metric projections are never paginated. Corrections update these
current representations and every current metric projection; this API provides no historic-as-of
record or metric view.

`GET /api/v1/spinning/records/{family}/{record_id}` returns one authorized current representation.
Every representation has `record_id`, `family`, integer `version`, `business_date`, `shift_code`, and
`captured_at`, plus `foreman_user_id` where recorder attribution applies. It includes the exact
family members defined by the capture response: established Production Discharge and Progress members,
the profile interpretation for Quality, and the Skeining and Waste members above. Calculated decimals
remain JSON strings.

`GET /api/v1/spinning/records/{family}/{record_id}/corrections` returns
`{"record_id":"…","family":"…","items":[…]}`. Every item has `correction_id`, integer
`version`, `corrected_at`, `corrected_by_user_id`, `reason`, `before`, and `after`; `before` and
`after` are complete family business snapshots, not field diffs. A record cannot be disclosed through
either read endpoint without the applicable authorization.

#### Metric filters

`GET /api/v1/spinning/sections/{section}/metrics` derives both section identity and read scope from
`{section}`. `GET /api/v1/spinning/consolidated/metrics` has no client-selected section filter: it
returns the sections authorized for the caller. Both accept only
`business_date_from`, `business_date_to`, `shift_code`, `machine_id`, `machine_group_id`, and
`yarn_count_id`.

All supplied filters use AND semantics. Dates are inclusive `YYYY-MM-DD` bounds; identifier and
shift values use exact-match normalization. A filter applies only to source records that carry that
dimension: `machine_id` and `yarn_count_id` apply to Production Discharge, Progress, and Skeining;
`machine_group_id` applies to Waste; date and shift apply to every v1 metric source. The service
rejects a filter when no metric source in the requested view can carry it (for example,
`machine_group_id` for Skeining), rather than silently ignoring it. It also rejects a `machine_id` or
`yarn_count_id` filter for a section whose applicable metrics have no source carrying that dimension.
No filter is accepted for Process Quality because Quality aggregations are outside v1.

#### Metric response model

Each section uses the same reusable row shape:

```json
{
  "section": "preparation",
  "metrics": [
    {
      "metric": "total_discharged_kg",
      "value": "125.400",
      "unit": "kg",
      "availability": "available"
    },
    {
      "metric": "skein_count",
      "value": null,
      "unit": "count",
      "availability": "not_applicable",
      "reason": "metric_not_applicable"
    }
  ]
}
```

Every row contains all seven v1 metric names in this order:
`total_discharged_kg`, `discharge_count`, `average_discharge_kg`, `skein_count`,
`estimated_skein_weight_kg`, `net_process_production_kg`, and `real_waste_kg`. Every metric has
`metric`, `value`, `unit`, and `availability`; it may also have the machine-readable `reason`.
Decimal values are JSON strings, `discharge_count` and `skein_count` are JSON integers, and values
for `not_applicable` or `unavailable` are `null`. The only availability values are `available`,
`zero`, `not_applicable`, and `unavailable`.

The exact successful section response is one section row as shown above. The exact successful
consolidated response is:

```json
{
  "sections": [
    {
      "section": "preparation",
      "metrics": ["the complete section metric row defined above"]
    }
  ]
}
```

The consolidated response contains one row for every authorized Yarn Spinning section and no row for
an unauthorized section. It never returns a `not_authorized` metric or section: authorization either
omits protected consolidated data or denies the requested resource under the shared error contract.

#### Metric sources, formulas, and no-data semantics

| Metric | Applies to | Current source family and formula |
| --- | --- | --- |
| `total_discharged_kg` | Preparation, Ring Spinning, Bobbin Winding, Twisting | Sum current Production Discharge `net_weight_kg`. |
| `discharge_count` | Preparation, Ring Spinning, Bobbin Winding, Twisting | Count current Production Discharge records. |
| `average_discharge_kg` | Preparation, Ring Spinning, Bobbin Winding, Twisting | `total_discharged_kg / discharge_count`; it is available only when the count is greater than zero. |
| `skein_count` | Skeining | Sum current Skeining `skein_count`. |
| `estimated_skein_weight_kg` | Skeining | Sum current Skeining `estimated_total_weight_kg`; each source value is server-calculated from skein count and estimated unit weight. |
| `net_process_production_kg` | Preparation, Ring Spinning, Twisting | Sum current Progress net process production: `output_weight_kg + discharged_weight_kg - input_weight_kg`. |
| `real_waste_kg` | Every productive section | Sum current Waste `waste_weight_kg`. |

`not_applicable` with `reason: "metric_not_applicable"` is returned for a metric outside the
section's listed applicability. `unavailable` with `reason: "no_current_records"` is returned when
the filtered current source record set is absent; absence is never evidence of zero. `zero` is
returned only when current source records exist and their applicable calculated aggregate is exactly
zero. Otherwise the calculated metric is `available`. These projections do not invent a transversal
“total production.”

Effective hours, productivity, waste rate, spindle utilization, planning, and all Quality
aggregations or comparisons across profile versions are deferred from v1.

### Corrections and Current State

`PATCH /api/v1/spinning/{family}/{record_id}` addresses one stable record in `production_discharge`,
`progress`, `process_quality`, `skeining`, or `waste`. Its exact request envelope is
`{"expected_version":4,"reason":"Corrected transcription error.","changes":{...}}`.
`expected_version` is the integer `version` returned by the latest authorized read and is mandatory;
`reason` is nonblank; `changes` contains only correctable business members for that family.

Server-owned identifiers, authoritative scope/context, attribution, timestamps, calculated values,
and `version` are forbidden in `changes`. Quality also forbids `profile_id` and `profile_version`;
it may change only profile-permitted capture values, `parameters`, and `observations`, and is
recalculated under its retained profile version. Skeining may change `machine_id`, `yarn_count_id`,
`skein_count`, `estimated_unit_weight_g`, `operator_name`, and `observations`. Waste may change
`section_id`, `machine_group_id`, `business_date`, `shift_code`, `waste_weight_kg`, and
`observations`. The server applies the PRD correction window and authorization, and returns the
complete corrected current representation with incremented `version`.

A successful correction updates the record's current values while preserving its original capture timestamp and appending immutable evidence for that changed business record: authenticated correcting actor, correction timestamp, reason, and complete before-and-after values. A Quality correction retains the original profile version and recalculates only under that version. Correction history is append-only. A multi-record correction may be atomic, but each changed business record retains its own evidence. A Progress input or output correction may return a continuity warning; it never automatically changes later records.

On `409 correction_concurrency_conflict`, `error.fields` remains an array of `{path, message}` only:
the shared Error Contract does not permit embedding `current_record`. The documented follow-up is
`GET /api/v1/spinning/records/{family}/{record_id}`, then an explicit client rebase and retry.

### Response Statuses and Errors

Successful creates return `201`; reads and successful corrections return `200`. The shared envelope is always used for errors:

```json
{
  "error": {
    "code": "domain_validation_error",
    "message": "The request violates an operational rule.",
    "fields": [
      { "path": "discharges.0.gross_weight_kg", "message": "Must be a valid value." }
    ]
  }
}
```

`error.fields` uses dot paths and zero-based array indexes. The following Yarn-Spinning outcomes use the shared envelope; codes are stable public identifiers.

| HTTP | Code | Contractual condition |
| --- | --- | --- |
| `400` | `request_validation_error` | Malformed JSON. |
| `403` | `authorization_denied` | The authenticated user lacks the required action in the server-derived scope. |
| `404` | `record_not_found` | The requested authorized record does not exist. |
| `409` | `continuity_conflict` | A Progress capture conflicts with an existing Progress record for the same section + machine + business date + shift + yarn count identity; the caller follows the authorized record read path for review. |
| `409` | `correction_concurrency_conflict` | The submitted `expected_version` is stale; neither current state nor correction evidence changes. |
| `422` | `request_validation_error` | Strict request-schema validation fails. |
| `422` | `domain_validation_error` | A PRD operational rule, applicability rule, calculation precondition, reconciliation requirement, or correction-window rule rejects the request. |

Errors never expose protected records, internal calculation mechanics, storage details, SQL, stack traces, or secrets.

## Authorization, Consistency, and Verification

Authorization occurs before protected mutation or disclosure. Section production and section metrics derive scope from the addressed section; Process Quality, Waste, and the consolidated projection use their respective transversal scopes. Yarn Spinning neither accepts client-authoritative scopes nor defines Access Control roles or policy.

Section-production capture succeeds completely or fails completely across every included applicable family. Concurrent attempts preserve first-save-wins behavior for a continuity key; the competing attempt is rejected without silent overwrite. Process Quality and Waste remain independent captures.

Any continuity-preparation response is advisory for display only. During the capture transaction, the
server re-resolves derived Progress input from current corrected state instead of trusting a stale
preparation response. Existing atomic capture behavior and `continuity_conflict` (`409`) behavior
remain unchanged.

Observable verification includes:

- decimal strings preserve declared units and counts are JSON integers;
- an authorized discharge response returns one stable ID per distinct discharge event, even when apparent context dimensions match;
- an authorized record response returns server-derived attribution where applicable and never accepts `foreman_user_id` from capture input;
- Progress reads return derived input, discharged, and output weights; those values are not accepted as client input;
- profile discovery returns only authorized, applicable active versions for new Quality capture, while
  authorized historical Quality reads retain retired profile versions and their interpretation data;
- Quality capture rejects unknown, inactive, inapplicable, client-calculated, and arbitrary-formula
  inputs, and returns server-recalculated decimal-safe results and tolerances; and
- a continuity-preparation read for an applicable Progress context returns server-resolved input and
  editable predecessor suggestions without persistence, while capture re-resolves the input; and
- a stale `expected_version` produces `correction_concurrency_conflict` without changing the record or evidence; and
- an authorization denial prevents protected disclosure or mutation.

## Out of Scope

- Shared Reference Data administration, yarn-count notation formats, and yarn-count characteristics beyond read-only reference use.
- Warehouse custody, lot assembly, lot-stage history, final lot quality, finished-product handoff, and cross-context reservation or allocation.
- Access Control taxonomy and evaluation, frontend interaction design, dashboard design, and client-side validation policy.
- Storage design, database schema, migrations, SQL, and implementation narrative.
