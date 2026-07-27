---
document_type: conceptual-model
status: active
implementation: not-started
scope: yarn-production
authority: conceptual
owner: architecture
last_reviewed: 2026-07-27
---

# Yarn Production DB Dictionary

This dictionary is a concise review aid for the current Yarn Production DBML. The model is hybrid, but primarily record-centered: it preserves the business records used in Hilatura without inventing a production run, machine-shift context, lot aggregate, or lot timeline. Yarn count is treated as a shared Catalogs identity and referenced from operational records.

## Review focus

- Continuity is by section, machine, shift, business date, and `yarn_count_id`.
- Production before Madejeras is recorded as discharges; Madejeras is recorded separately as skein output.
- Progress, process quality, and waste stay as their own record families.
- Yarn count characteristics such as material type, dtex, and business labels belong to Catalogs, not to every Yarn Production record.
- Current business records can be corrected, but correction history is stored separately.
- No SQL, indexing, ORM mapping, or reporting aggregate is defined here.

## Tables

### `yarn_production_machines`

Represents the machines used by Yarn Production sections.

| Field          | Why it exists                                                       | Optional / challenge later          |
| -------------- | ------------------------------------------------------------------- | ----------------------------------- |
| `machine_id`   | Technical identifier for records that need a machine reference.     | No.                                 |
| `section`      | Keeps each machine tied to its production section.                  | No.                                 |
| `machine_code` | Visible plant code operators recognize.                             | No; exact format may change.        |
| `machine_name` | Human-readable label.                                               | Yes.                                |
| `is_active`    | Prevents old machines from being selected without deleting history. | Yes; could move to a catalog later. |
| `created_at`   | System timestamp.                                                   | No.                                 |

### `production_discharges`

Represents one production discharge for Preparation FIN machines, Ring Spinning, Bobbin Winding, or Twisting.

| Field                                                                             | Why it exists                                                    | Optional / challenge later                         |
| --------------------------------------------------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------- |
| `production_discharge_id`                                                         | Technical identifier for the discharge record.                   | No.                                                |
| `section`, `machine_id`                                                           | Locate the producing section and machine.                        | No; validate Preparation only allows FIN machines. |
| `business_date`, `shift_code`                                                     | Preserve operational time separate from system capture.          | No.                                                |
| `supervisor_user_id`                                                              | Shift supervision reference.                                     | No.                                                |
| `yarn_count_id`                                                                   | References the shared Catalogs yarn count identity produced.      | No.                                                |
| `discharged_at`                                                                   | Physical discharge time when captured.                           | Yes.                                               |
| `gross_weight_kg`, `spindle_tare_kg`, `operative_spindle_count`, `cart_weight_kg` | Inputs for the discharge weight calculation.                     | No for sections using spindle/cart calculation.    |
| `net_weight_kg`                                                                   | Calculated production result preserved for reporting and review. | No.                                                |
| `roving_count`                                                                    | Preparation-specific mecha count when captured.                  | Yes.                                               |
| `registered_by_user_id`, `registered_role`                                        | Who recorded it and under which operational role.                | No.                                                |
| `notes`                                                                           | Operational context or exceptions.                               | Yes.                                               |
| `created_at`, `updated_at`                                                        | System capture and last update timestamps.                       | Created no; updated yes.                           |

### `skein_records`

Represents Madejeras/Skeining production output. It is a business record of skeins produced, not a lot or availability aggregate.

| Field                                      | Why it exists                                                    | Optional / challenge later                               |
| ------------------------------------------ | ---------------------------------------------------------------- | -------------------------------------------------------- |
| `skein_record_id`                          | Technical identifier for the skein production record.            | No.                                                      |
| `machine_id`                               | Madejeras machine that produced the skeins.                      | No.                                                      |
| `business_date`, `shift_code`              | Operational continuity.                                          | No.                                                      |
| `supervisor_user_id`                       | Shift supervision reference.                                     | No.                                                      |
| `yarn_count_id`                            | References the shared Catalogs yarn count identity produced.      | No.                                                      |
| `skein_count`                              | Primary Madejeras production quantity.                           | No.                                                      |
| `unit_skein_weight_kg`                     | Estimated unit weight used for this record's calculation.        | No; wording may need refinement for monio-based capture. |
| `estimated_weight_kg`                      | Calculated total estimated weight.                               | No.                                                      |
| `weight_requirement_note`                  | Explains title-specific weight differences such as 500g vs 600g. | Yes.                                                     |
| `registered_by_user_id`, `registered_role` | Who recorded it and under which operational role.                | No.                                                      |
| `notes`                                    | Operational context or exceptions.                               | Yes.                                                     |
| `created_at`, `updated_at`                 | System capture and last update timestamps.                       | Created no; updated yes.                                 |

### `progress_records`

Represents the section progress summary for Preparation, Ring Spinning, and Twisting.

| Field                                       | Why it exists                                                | Optional / challenge later                                       |
| ------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------- |
| `progress_record_id`                        | Technical identifier for the progress record.                | No.                                                              |
| `section`, `machine_id`                     | Locate the section and machine.                              | No; Bobbin Winding and Skeining should not use progress records. |
| `business_date`, `shift_code`, `yarn_count_id` | Continuity key used to reconcile with production discharges. | No.                                                              |
| `input_weight_kg`                           | Material entering the machine/section.                       | No.                                                              |
| `in_machine_net_weight_kg`                  | Material still in the machine when captured.                 | Yes; mainly Ring Spinning and Twisting.                          |
| `discharged_weight_kg`                      | Summary amount expected to reconcile with discharge totals.  | No.                                                              |
| `output_weight_kg`                          | Material leaving the section.                                | No.                                                              |
| `operative_spindle_count`                   | Supports spindle-sampling calculations where applicable.     | Yes.                                                             |
| `worked_hours`                              | Supports productivity metrics.                               | Yes.                                                             |
| `registered_by_user_id`, `registered_role`  | Who recorded it and under which operational role.            | No.                                                              |
| `consistency_notes`                         | Reconciliation or operational notes.                         | Yes.                                                             |
| `created_at`, `updated_at`                  | System capture and last update timestamps.                   | Created no; updated yes.                                         |

### `process_quality_records`

Represents process quality checks across all Yarn Production sections.

| Field                                         | Why it exists                                               | Optional / challenge later                               |
| --------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------- |
| `process_quality_record_id`                   | Technical identifier for the quality record.                | No.                                                      |
| `section`, `machine_id`                       | Locate the checked section and, when applicable, machine.   | Machine can be optional for section-level random checks. |
| `business_date`, `shift_code`                 | Operational time of the check.                              | No.                                                      |
| `yarn_count_id`                               | Yarn count identity or sample context when relevant.         | Yes.                                                     |
| `quality_method`                              | Distinguishes samples, machine counters, and random checks. | No.                                                      |
| `sample_type`, `sample_count`                 | Sample-based quality context.                               | Yes.                                                     |
| `cv_percent`, `tenacity`, `elongation`        | Sample result values used in Preparation/Ring Spinning.     | Yes.                                                     |
| `body_value`, `kilometers`, `cuts_per_bobbin` | Bobbin Winding machine-counter values.                      | Yes.                                                     |
| `result_summary`                              | Flexible summary for variable random checks.                | Yes; replace with structured fields only when stable.    |
| `is_out_of_tolerance`                         | Quick review flag.                                          | Yes.                                                     |
| `registered_by_user_id`                       | Quality user who recorded the check.                        | No.                                                      |
| `notes`                                       | Quality context or exception notes.                         | Yes.                                                     |
| `created_at`, `updated_at`                    | System capture and last update timestamps.                  | Created no; updated yes.                                 |

### `waste_records`

Represents real or accumulated waste recorded by section and shift.

| Field                                      | Why it exists                                      | Optional / challenge later                                    |
| ------------------------------------------ | -------------------------------------------------- | ------------------------------------------------------------- |
| `waste_record_id`                          | Technical identifier for the waste record.         | No.                                                           |
| `section`                                  | Section where the waste belongs.                   | No.                                                           |
| `machine_group_name`                       | Snapshot of the group weighed together.            | Yes for Madejeras; challenge if groups become a real catalog. |
| `business_date`, `shift_code`              | Operational time.                                  | No.                                                           |
| `waste_type`                               | Real vs accumulated waste.                         | No.                                                           |
| `weight_kg`                                | Waste quantity.                                    | No.                                                           |
| `registered_by_user_id`, `registered_role` | Who recorded it and under which operational role.  | No.                                                           |
| `notes`                                    | Context, exceptions, or Madejeras reproceso notes. | Yes.                                                          |
| `created_at`, `updated_at`                 | System capture and last update timestamps.         | Created no; updated yes.                                      |

### `yarn_production_record_corrections`

Represents audit history for controlled edits to Yarn Production records.

| Field                           | Why it exists                                           | Optional / challenge later                       |
| ------------------------------- | ------------------------------------------------------- | ------------------------------------------------ |
| `correction_id`                 | Technical identifier for the audit entry.               | No.                                              |
| `record_table`, `record_id`     | Identifies the corrected current business record.       | No; polymorphic by design to keep audit minimal. |
| `corrected_by_user_id`          | Actor who made the correction.                          | No.                                              |
| `corrected_at`                  | System time of correction.                              | No.                                              |
| `correction_reason`             | Required business reason for the edit.                  | No.                                              |
| `authorization_basis`           | Operational window, SysAdmin override, or policy basis. | Yes but recommended.                             |
| `before_values`, `after_values` | Full before/after evidence.                             | No.                                              |
| `created_at`                    | System timestamp for the audit row.                     | No.                                              |
