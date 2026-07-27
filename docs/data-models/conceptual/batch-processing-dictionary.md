---
document_type: conceptual-model
status: active
implementation: not-started
scope: batch-processing/lot-processing
authority: conceptual
owner: architecture
last_reviewed: 2026-07-27
---

# Batch Processing DB Dictionary

This dictionary is a concise review aid for the current Batch Processing DBML. Warehouse defines the single lot identity; each stage records only the facts it owns or verifies for that same lot.

## Review focus

- Every stage table references the Warehouse-defined `production_identity_id` directly.
- Stage records are separate because Inventory, Dyeing, Drying, Winding/Balling, Bagging, and Quality capture different business facts.
- Each table may contain multiple records for the same lot. The lot's process history is the axis: `business_date`, `shift_code`, actors, and timestamps describe an intervention and are never a uniqueness key.
- Later stages require completion of the prior stage. This is a use-case/domain invariant across specialized tables, enforced by application logic rather than cross-table DBML constraints.
- Notes are optional fields inside the relevant stage records, not a standalone table.
- Waste is not generalized. It stays on Winding/Balling and Bagging, where the current process clearly records conversion or packing waste.
- Quality Send evidence and an optional Warehouse pending-receipt note stay in `lot_quality_records`. `quality_sent_to_warehouse_at` is the singular explicit send marker: at most one Quality record per `production_identity_id` may set it. PostgreSQL must enforce this with `CREATE UNIQUE INDEX lot_quality_records_one_quality_send_per_lot_idx ON lot_quality_records (production_identity_id) WHERE quality_sent_to_warehouse_at IS NOT NULL`; DBML cannot express a partial unique index. The sent handoff is pending until Warehouse records its one `finished_product_receipts` row for the same `production_identity_id`; that receipt's unique `production_identity_id` rejects a second acceptance. No timestamp ordering or tie-breaker selects a handoff.
- Current business records can be corrected, but correction history is stored separately and lean.
- No SQL, indexing, ORM mapping, or reporting aggregate is defined here.

## Tables

### Lot identity

Warehouse owns the single `production_identity_id` and its visible `lot_code`; Lot Processing stores neither a duplicate aggregate nor duplicated defining fields.

Warehouse's initial definition of this identity preserves the business meaning formerly expressed by `warehouse_defined`; it is not a Lot Processing state.


### `inventory_stage_records`

Represents the physical assembly of the lot by Inventory.

| Field                                        | Why it exists                                           | Optional / challenge later                                  |
| -------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------- |
| `inventory_stage_record_id`                  | Technical identifier for the Inventory stage record.    | No.                                                         |
| `production_identity_id`                     | Connects the stage record to the Warehouse-defined lot history. | No; multiple Inventory records may belong to the same lot. |
| `business_date`, `shift_code`                | Preserve operational time separate from system capture. | No.                                                         |
| `assembled_by_user_id`, `supervisor_user_id` | Who assembled the lot and who supervised the shift.     | No.                                                         |
| `skein_count`                                | Number of skeins physically assembled.                  | No.                                                         |
| `total_weight_kg`                            | Weight of the assembled physical lot.                   | No.                                                         |
| `assembly_issue_category`                    | Structured issue category when assembly has problems.   | Yes; replace with a catalog only when categories stabilize. |
| `notes`                                      | Optional operational context.                           | Yes.                                                        |
| `created_at`, `updated_at`                   | System capture and last update timestamps.              | Created no; updated yes.                                    |

### `dyeing_stage_records`

Represents color application in Dyeing.

| Field                                                               | Why it exists                                                        | Optional / challenge later                                          |
| ------------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `dyeing_stage_record_id`                                            | Technical identifier for the Dyeing stage record.                    | No.                                                                 |
| `production_identity_id`                                            | Connects Dyeing to the Warehouse-defined lot history.                | No; multiple Dyeing records may belong to the same lot.            |
| `business_date`, `shift_code`                                       | Operational time for the stage.                                      | No.                                                                 |
| `received_by_user_id`, `delivered_by_user_id`, `supervisor_user_id` | Captures responsibility across receipt, handoff, and supervision.    | Receiver and supervisor no; deliverer can be filled at stage close. |
| `received_skein_count`                                              | What Dyeing received from Inventory.                                 | No.                                                                 |
| `inherited_weight_kg`, `measured_weight_kg`                         | Separates inherited weight from real local measurement.              | Both context-dependent; do not force fake weighing.                 |
| `vat_number`                                                        | Identifies the vat used for dyeing.                                  | No.                                                                 |
| `process_temperature`                                               | Captures process temperature when relevant.                          | Yes; may become required by policy.                                 |
| `requires_redye`                                                    | Records whether a second dyeing pass is needed.                      | No.                                                                 |
| `issue_category`                                                    | Structured issue category such as redye or temperature out of range. | Yes.                                                                |
| `output_condition_note`, `notes`                                    | Stage exit condition and optional context.                           | Yes.                                                                |
| `created_at`, `updated_at`                                          | System capture and last update timestamps.                           | Created no; updated yes.                                            |

### `drying_stage_records`

Represents drying after Dyeing.

| Field                                                               | Why it exists                                                     | Optional / challenge later                                          |
| ------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| `drying_stage_record_id`                                            | Technical identifier for the Drying stage record.                 | No.                                                                 |
| `production_identity_id`                                            | Connects Drying to the Warehouse-defined lot history.             | No; multiple Drying records may belong to the same lot.            |
| `business_date`, `shift_code`                                       | Operational time for the stage.                                   | No.                                                                 |
| `received_by_user_id`, `delivered_by_user_id`, `supervisor_user_id` | Captures responsibility across receipt, handoff, and supervision. | Receiver and supervisor no; deliverer can be filled at stage close. |
| `received_skein_count`                                              | What Drying received from Dyeing.                                 | No.                                                                 |
| `measured_input_weight_kg`                                          | Local weight only when the stage really measures it.              | Yes; avoid simulated data.                                          |
| `moisture_issue_category`                                           | Structured issue category such as excessive humidity.             | Yes.                                                                |
| `output_condition_note`, `notes`                                    | Stage exit condition and optional context.                        | Yes.                                                                |
| `created_at`, `updated_at`                                          | System capture and last update timestamps.                        | Created no; updated yes.                                            |

### `winding_stage_records`

Represents conversion from skeins into cones or balls.

| Field                                                               | Why it exists                                                       | Optional / challenge later                                          |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `winding_stage_record_id`                                           | Technical identifier for the Winding/Balling stage record.          | No.                                                                 |
| `production_identity_id`                                            | Connects the conversion stage to the Warehouse-defined lot history. | No; multiple Winding/Balling records may belong to the same lot.   |
| `business_date`, `shift_code`                                       | Operational time for the stage.                                     | No.                                                                 |
| `received_by_user_id`, `delivered_by_user_id`, `supervisor_user_id` | Captures responsibility across receipt, handoff, and supervision.   | Receiver and supervisor no; deliverer can be filled at stage close. |
| `conversion_variant`                                                | Distinguishes winding to cones from balling to balls.               | No.                                                                 |
| `received_skein_count`                                              | Skeins received for conversion.                                     | No.                                                                 |
| `produced_unit_count`                                               | Cones or balls produced.                                            | No.                                                                 |
| `waste_quantity`, `waste_unit`, `waste_cause`                       | Stage-owned waste generated during conversion.                      | Yes; clarify whether waste is kg, units, or both.                   |
| `issue_category`                                                    | Structured issue category such as damaged cones or excessive waste. | Yes.                                                                |
| `output_condition_note`, `notes`                                    | Stage exit condition and optional context.                          | Yes.                                                                |
| `created_at`, `updated_at`                                          | System capture and last update timestamps.                          | Created no; updated yes.                                            |

### `bagging_stage_records`

Represents packing the cones or balls before Quality.

| Field                                                               | Why it exists                                                                       | Optional / challenge later                                          |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `bagging_stage_record_id`                                           | Technical identifier for the Bagging stage record.                                  | No.                                                                 |
| `production_identity_id`                                            | Connects Bagging to the Warehouse-defined lot history.                            | No; multiple Bagging records may belong to the same lot.           |
| `business_date`, `shift_code`                                       | Operational time for the stage.                                                     | No.                                                                 |
| `received_by_user_id`, `delivered_by_user_id`, `supervisor_user_id` | Captures responsibility across receipt, handoff, and supervision.                   | Receiver and supervisor no; deliverer can be filled at stage close. |
| `received_unit_count`                                               | Cones or balls received from Winding/Balling.                                       | No.                                                                 |
| `bag_count`, `units_per_bag`                                        | Packing result.                                                                     | No.                                                                 |
| `waste_quantity`, `waste_unit`, `waste_cause`                       | Stage-owned waste generated during bagging.                                         | Yes; clarify whether waste is kg, units, or both.                   |
| `issue_category`                                                    | Structured issue category such as damaged bags, incorrect label, or count mismatch. | Yes.                                                                |
| `output_condition_note`, `notes`                                    | Stage exit condition and optional context.                                          | Yes.                                                                |
| `created_at`, `updated_at`                                          | System capture and last update timestamps.                                          | Created no; updated yes.                                            |

### `lot_quality_records`

Represents final Quality inspection, the one permitted Quality Send marker, and any Warehouse coordination note while the lot awaits Warehouse validation. Warehouse acceptance is recorded separately by `finished_product_receipts` for the same `production_identity_id`.

| Field                                                            | Why it exists                                                                   | Optional / challenge later                                      |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `lot_quality_record_id`                                          | Technical identifier for the Quality stage record.                              | No.                                                             |
| `production_identity_id`                                         | Connects Quality to the Warehouse-defined lot history.                          | No; multiple Quality records may belong to the same lot, but only one may carry the send marker. |
| `business_date`, `shift_code`                                    | Operational time of the inspection.                                             | No.                                                             |
| `inspected_by_user_id`, `supervisor_user_id`                     | Quality responsibility and supervision.                                         | No.                                                             |
| `visual_defect_categories`, `internal_defect_categories`         | Defects reported by Quality before handoff.                                     | Yes as text for now; normalize only after categories stabilize. |
| `quality_state`                                                  | Operation quality state at handoff: standard, special nomenclature, or flagged. | No.                                                             |
| `special_nomenclature`                                           | Policy-specific nomenclature assigned by Quality.                               | Yes.                                                            |
| `delivery_condition_note`                                        | Conditions reported to Warehouse.                                               | Yes.                                                            |
| `quality_sent_to_warehouse_at`, `quality_sent_to_warehouse_by_user_id` | Exact time and Quality actor for the one permitted send to Warehouse. | Yes; `quality_sent_to_warehouse_at` is the explicit send marker. PostgreSQL enforces at most one non-null marker per `production_identity_id` with the documented partial unique index; `business_date` remains the UI-facing operational date. |
| `warehouse_note`, `noted_by_user_id`, `warehouse_noted_at`        | Brief Warehouse coordination note, actor, and time on the singular sent handoff before a Warehouse receipt exists for the same `production_identity_id`. The note does not mean acceptance, create a resend, or change identity; the actor is an audit fact, not a permission source. | Yes; allowed only while that singular handoff is pending. |
| `notes`                                                          | Optional quality context.                                                       | Yes.                                                            |
| `created_at`, `updated_at`                                       | System capture and last update timestamps.                                      | Created no; updated yes.                                        |

### `batch_processing_record_corrections`

Represents audit history for controlled edits to Batch Processing records.

| Field                                  | Why it exists                                                  | Optional / challenge later                       |
| -------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------ |
| `correction_id`                        | Technical identifier for the audit entry.                      | No.                                              |
| `record_table`, `record_id`            | Identifies the corrected current business record.              | No; polymorphic by design to keep audit minimal. |
| `corrected_by_user_id`, `corrected_at` | Who corrected the record and when the correction was captured. | No.                                              |
| `correction_reason`                    | Required business reason for the correction.                   | No.                                              |
| `authorization_basis`                  | Operational window, SysAdmin override, or other policy basis.  | Yes but recommended.                             |
| `before_values`, `after_values`        | Full before/after evidence.                                    | No.                                              |
| `created_at`                           | System timestamp for the audit row.                            | No.                                              |
