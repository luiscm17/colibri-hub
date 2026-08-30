---
document_type: technical-spec
status: draft
scope: operation/yarn-spinning
authority: explanatory
owner: frontend
last_reviewed: 2026-08-28
replaces: null
---

# Frontend Yarn Spinning

## Purpose and Boundary

Yarn Spinning supports authorized operational capture, review, and correction of production,
progress, skeining, process-quality, and waste information, plus read-only section and consolidated
reporting. It owns coherent user journeys, presentation, and interaction state; server-confirmed
outcomes and calculated values remain authoritative and read-only.

It does not own business or authorization policy, shared-reference administration, persistence, or
transport contracts. Process Quality and Waste are independent transversal experiences, not sub-forms
of section production capture. Skeining capture remains separate from Lot Processing.

## Authorities

The [Yarn Spinning PRD](../../../docs/prd/operation/yarn-spinning.md) governs business rules, record
semantics, calculations, identity, validation, correction semantics, and acceptance criteria. The
frontend reflects server authorization for correction affordances and results; it does not define
authorization policy. When frontend behavior differs from an authoritative server result or the PRD,
that authority prevails.

## Architectural References

Yarn Spinning follows the [Frontend Architecture Overview](../architecture/overview.md), [Technology Baseline](../../../docs/architecture/technology-baseline.md), [Frontend Styling](../../../docs/dev-guide/frontend-styling.md), [Visual Identity](../design-system/visual-identity.md), [Accessibility Guidelines](../accessibility.md), and [Frontend Testing Strategy](../testing/strategy.md) without restating these transversal authorities.

## User-Visible Capabilities

- Section workspaces establish a business-date and shift context and support applicable production
  and progress capture as one shift-close outcome. Their header/capture context provides one
  operational supervisor selection, applied to every applicable record submitted from that capture.
- Process Quality and Waste provide separate server-authorized capture and review experiences.
- Section and consolidated dashboards provide read-only operational results in a retained reporting
  context.
- Corrections let authorized users review an existing and proposed outcome, provide required
  rationale, and receive a confirmed or recoverable result.

## Capability Collaboration Boundaries

Shared Reference Data supplies read-only choices for capture and reporting context; Yarn Spinning
neither duplicates nor administers them. Authoritative services validate requests, preserve records,
calculate results, and decide request outcomes. Other frontend capabilities use intentional
user-facing integration points rather than this capability's internals.

## Interaction States and Outcomes

The selected business-date and shift stay visible while work is in progress; changing them requires
an explicit action. One operational supervisor is selected in the section workspace header/capture
context and applies to all applicable records submitted from that capture. The authenticated session
supplies foreman/recorder attribution, which may appear as non-editable context; the frontend neither
edits nor sends that attribution. Users may enter or amend only values allowed by server
authorization. Derived values update with
relevant inputs but are confirmed by the authoritative result.

Production capture supports keyboard-oriented entry, appropriate paste, inline feedback, and clear
summaries. Repeat discharges with matching production dimensions remain distinct events. Numeric
input distinguishes explicit zero from incomplete or unknown input; a blank machine remains pending
 and never implies zero, while an acknowledged machine visibly shows “Sin producción — cero
  confirmado”. The acknowledgement is reversible until submission and protects capture completeness
only: it is not a production record or independently auditable event. Acknowledged no-production
machines are omitted from submitted production data; the authoritative service alone applies any
PRD-defined zero semantics and determines the resulting business outcome.

Progress shows predecessor-derived opening input when available, otherwise zero; output is the sole
closing in-machine quantity and net process production is derived. The difference between input and
output is not presented as waste. Process Quality first shows applied profile and version context,
then renders only its dynamic fields or rows, units, capture mode, results, and tolerances. A Sample
profile uses an ordered React Data Grid for its configured 10–15 measurements. Preparation displays
two readonly result cells and immediate informative preview; the UI does not hardcode their variable
names, formulas, or units. Machine Register and Random retain their applicable methods but are also
profile-driven. Waste capture records independently weighed real
waste by machine group and shift; theoretical or accumulated waste is excluded, and
out-of-specification skeins are reprocessing rather than waste.

Section production and progress submit together; Process Quality and Waste submit independently.
Loading, empty, populated, recoverable-failure, unavailable-access, and conflict states are distinct.
Reporting retains filters for empty results and does not present superseded results as current.

### Progress Continuity Prefill

Only a new Progress capture whose applicability is resolved by authorized catalog/configuration and
the server response receives an automatic, visible continuity prefill. For its selected section,
machine, and yarn-count identity, the interface shows the server-derived input weight and identifies
it as the preceding logical Progress output. It also presents the predecessor's operative spindle
count and worked hours as editable suggestions.

Changing the machine or yarn-count identity invalidates the visible derived input while the interface
requests continuity for the new configuration. The response is applied only if it still matches the
current configuration, preventing a stale response from replacing a newer selection. A read failure
preserves the local draft and shows recoverable feedback. A valid no-predecessor response visibly
shows zero input without blocking capture; a changed or new yarn-count identity normally has no
predecessor because it is a new stream.

This prefill never applies to Production Discharge events, including repeated events, and never
copies discharge events or weights, samples, Quality, Waste, Skeining, calculated values, or
dashboard data. The existing UI-only “Sin producción — cero confirmado” acknowledgement remains
separate from continuity prefill.

## Server-Authorization Behavior

Capture and correction affordances reflect server authorization. Unavailable destinations are not
actionable; unavailable actions are hidden or disabled with an understandable reason where
appropriate. A returned authorization failure stops the protected action and remains non-retryable
until authorized context is refreshed.

Correction affordances and results follow server authorization. Yarn Spinning rules govern
correction semantics; the interface does not decide correction validity.

Process Quality exposes a profile configuration surface only after a server-authorized outcome. It
lets users select from backend-approved calculation operations and manage profile lifecycle and
applicability; it never exposes an arbitrary formula editor. Capture and correction remain separate
from configuration.

## MVP Dashboard Read Contract

The dashboard is a read-only experience separate from capture. It consumes server-calculated section
and consolidated metric projections and retains selected business-date bounds, shift, machine,
machine-group, and yarn-count filters while results load, are empty, or recover from an error. It
never calculates, derives, or substitutes a metric in the browser.

The section dashboard consumes one section row. The consolidated dashboard consumes the same section
row shape as a matrix or section cards, showing only the sections returned by the authorized
consolidated projection. Each row presents the backend metric name, value, unit, and availability:

- `available` presents the returned value.
- `zero` presents the returned known zero.
- `not_applicable` presents an explicit not-applicable state.
- `unavailable` presents an explicit unavailable state and its returned reason when supplied.

An absent record set never becomes a displayed zero. Sections unavailable through server
authorization are omitted by the consolidated response or their destination is denied; the dashboard
never models a `not_authorized` metric or section.

Dashboard loading preserves filter context and announces loading status. An empty or unavailable
projection explains that no current source data is available without fabricating a value. A denied
destination follows the existing non-actionable authorization state. Recoverable service failures retain
filters, preserve the last confirmed results only when clearly identified as stale, and offer retry.
The matrix/cards use semantic section headings, accessible names for metric values and units,
programmatically exposed availability and reason text, visible focus, keyboard-reachable retry, and
non-color-only state distinctions.

This MVP includes only `total_discharged_kg`, `discharge_count`, `average_discharge_kg`,
`skein_count`, `estimated_skein_weight_kg`, `net_process_production_kg`, and `real_waste_kg` as
returned by the backend. Effective hours, productivity, waste rate, spindle utilization, planning,
Quality aggregations or comparisons across profile versions, charts, and dashboard layout decisions
remain outside v1.

## Drafts, Recovery, Errors, and Conflicts

Entered work is retained through validation, connectivity, service, and concurrency failures and is
cleared or replaced only after explicit user intent or confirmed success. Client feedback identifies
incomplete or malformed input before submission; server feedback is associated with the relevant
area when possible. Unconfirmed service outcomes offer a safe retry path.

Quality drafts retain the selected profile version and entered raw values. A changed profile context
invalidates incompatible draft fields with clear recovery guidance rather than silently remapping
them. Grid and dynamic-field validation identify ordered-row and parameter errors programmatically;
readonly results and tolerance status announce preview, validation, and server-confirmed changes.
The preview never replaces server confirmation, and a retired, unknown, or inapplicable profile is
shown as a recoverable server error while retaining the draft.

Conflicts never silently overwrite newer information. Local work is preserved, and a `409` during a
correction requires an authorized current-record read before the user or client rebases and retries.
The server-confirmed record is then shown for review. Corrections show the existing and proposed
outcomes, required rationale, retained evidence for each changed record, and original-capture
context. A server-provided progress-continuity warning makes no downstream change automatically;
any later action is a separate explicit decision.

## Security and Privacy Presentation Boundary

The interface reveals operational information and actions only as authorized by the server. It
presents server-confirmed records and correction evidence without inventing policy or collecting
unrelated information. The server remains authoritative for authorization, validation, retention, and
disclosure.

## Responsive Priority

Capture context, required inputs, validation, completion status, and review actions remain primary
across constrained viewports. Dense operational work prioritizes desktop and tablet efficiency while
remaining usable on smaller screens through controlled overflow and reachable controls; essential
capture and review information is not hidden.

## Accessibility

Primary flows meet WCAG 2.1 AA expectations: semantic labels, keyboard-operable controls, visible
focus, sufficient contrast, programmatically associated errors, announced status changes, and
non-color-only feedback. Keyboard users and assistive technology can operate capture, validation,
submission feedback, and conflict recovery.

## Observable Verification

- An authorized user establishes visible section context, completes applicable section work, and
  receives one section outcome; repeated discharges remain separate events. One operational
  supervisor selection is visible in the workspace header/capture context and applies to all
  applicable submitted records, while foreman/recorder attribution remains session-derived and
  non-editable.
- A blank/pending machine and “Sin producción — cero confirmado” are visibly distinct. The
  no-production acknowledgement is required before submission, can be reversed before submission,
  and does not itself produce a record or determine a business outcome.
- Submitted production data excludes acknowledged no-production machines; only actual records are
  submitted, and any zero interpretation remains subject to authoritative PRD-defined semantics.
- Progress, independent Process Quality methods, real-waste-only capture, and the skeining/Lot
  Processing boundary are presented as specified by the PRD.
- Process Quality shows profile/version context and profile-driven fields, rows, units, results, and
  tolerances. Preparation shows an ordered 10–15-row sample grid with two readonly result cells and
  immediate preview, while server confirmation remains authoritative.
- Quality draft, validation, authorization, retirement, and service-error states preserve entered raw
  values and provide accessible, programmatically associated feedback. Profile configuration appears
  only after a server-authorized outcome and permits no arbitrary formulas.
- A new Progress capture identified as applicable by authorized catalog/configuration and the server
  response visibly identifies its server-derived input source and presents predecessor spindle count
  and worked hours as editable suggestions. Configuration changes discard stale continuity responses,
  read failures preserve the draft, and a no-predecessor zero remains non-blocking.
- Protected destinations and actions follow server authorization; correction affordances and results
  follow that authorization, while Yarn Spinning rules govern the correction semantics. Correction
  review captures required rationale and presents continuity warnings without automatic downstream
  changes.
- Validation, service failure, conflict, loading, empty reporting, and populated reporting remain
  distinguishable, preserve appropriate work or context, and provide accessible feedback.

## Out of Scope

- Business-rule definitions, calculations, record identity, and family applicability.
- Authorization-policy definitions and evaluation.
- Persistence, transport contracts, server-side validation, and administration of reference data or
  operational parameters.
- Lot availability, allocation, reservation, consumption, and attribution; planning-data capture; and
  data migration.
