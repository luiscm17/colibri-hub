# Frontend Bale Management Exploration

**Status:** partial — sufficient architectural context exists, but several product and contract decisions must be resolved before proposal/design.

## Exploration: Frontend Bale Management Readiness

### Current State

The documentation provides a strong target for three dedicated frontend surfaces:

1. `/warehouse/bales/reception` — atomic reception of one batch and 1–100 bales.
2. `/warehouse/bales` — filtered aggregate stock metrics and composite-identity lookup.
3. `/warehouse/bales/delivery` — one delivery-date submission with 1–50 identities and per-bale results.

The normative business rules are clear in `docs/prd/warehouse/bale-management.md`. The frontend specification adds interaction, state, accessibility, decimal, grid, and error-mapping requirements. The backend specification supplies endpoint paths, methods, payload fields, response fields, status codes, and the common error vocabulary; backend source behavior is intentionally not used as evidence.

The current frontend is only an earlier reception prototype. Its `/warehouse/reception` route renders `ReceptionPage`, which captures truck/license, carrier, material, and lot fields and sends a legacy payload to `/api/warehouse/receptions`. Its row model uses JavaScript numbers, tare arrays, editable net weight, and legacy bale/lot concepts. It does not implement the documented bale-reception contract. The other warehouse routes currently point to the placeholder `WarehousePage`; the three bale routes and navigation entries do not exist.

The application shell, Mantine provider, authentication provider, lazy route pattern, feature folders, Mantine form usage, and `react-data-grid` dependency are present. The documented target `frontend/src/common/grid/` and the feature-specific `api/`, `model/`, and hook structure are not present. There is no frontend test runner, shared HTTP-client convention, or server-cache library configured.

### Affected Areas

- `docs/prd/warehouse/bale-management.md` — normative business rules, identities, dates, weights, lifecycle, queries, and acceptance criteria.
- `frontend/docs/features/bale-management.md` — target pages, UX flows, grid behavior, decimal strategy, API usage, accessibility, and implementation sequence.
- `backend/docs/features/bale-management.md` — documentation-only transport contract used for request/response shapes and error/status handling.
- `frontend/src/app/routes/index.tsx` — add three lazy-loaded bale routes; existing warehouse routes currently target placeholders or the legacy reception page.
- `frontend/src/app/routes/lazy-pages.ts` — expose the three page modules as lazy pages.
- `frontend/src/app/navigation-data.tsx` — add the three Warehouse navigation entries and settle their labels/routes.
- `frontend/src/features/warehouse/pages/ReceptionPage.tsx` and `frontend/src/features/warehouse/components/*` — legacy reception prototype must be replaced or isolated; its fields and payload contradict the target capability.
- `frontend/src/features/warehouse/hooks/*`, `types/*`, and `api/receptionApi.ts` — existing state, numeric types, endpoint, and error handling are not reusable as the target API boundary without substantial redesign.
- `frontend/src/common/components/*` — existing page state/header primitives can be reused, but the documented grid wrapper/editors/error indicators do not exist.
- `frontend/docs/architecture/overview.md` and `frontend/docs/patterns/data-grid.md` — provide conventions, but contain target-state gaps and a placement discrepancy for the shared grid wrapper (`common/grid/` versus `common/components/`).
- `frontend/package.json` — approved dependencies are sufficient for the documented implementation; no test, decimal, date, HTTP, or server-cache library is installed.

### Contract and Consistency Assessment

#### What is clear

- The PRD is the business authority; the frontend is a client and must not decide uniqueness, transitions, concurrency, or persistence policy.
- Reception sends `shipment_number`, `received_at` as `YYYY-MM-DD`, `provider_name`, and bales containing decimal strings for `dtex`, `gross_weight_kg`, and `container_weight_kg`; it does not send net weight.
- Registration returns HTTP 201 and a five-field summary: `raw_material_batch_id`, normalized shipment number, date, provider, and `bale_count`.
- Stock summary uses `GET /api/v1/warehouse/bales`, conjunctive optional filters, six metrics, zero-valued empty results, and decimal-string weights.
- Detail uses the composite path identity and returns the documented full detail, including calculated net weight and nullable delivery date; missing identity is 404 `bale_not_found`.
- Delivery sends one shared date and 1–50 composite identities to `POST /api/v1/warehouse/bales/deliver`; 200 means all success and 207 carries per-bale results (`delivered`, `already_delivered`, `not_found`).
- Reception and delivery preserve drafts after failures; only successful acknowledgement followed by explicit user action clears reception, while delivery keeps failed rows retryable.
- The grid must preserve decimal input as strings, support keyboard/paste workflows, maintain stable row IDs, distinguish empty/partial/valid/invalid rows, and expose accessible feedback.
- The current stack supports the target without adding libraries: React 19, Mantine 9, `@mantine/form`, `react-data-grid`, React Router 7, TypeScript, CSS Modules, and Tabler icons.

#### Is any alleged JSON contract actually specified?

**Yes, at the documentation level, but not as a single machine-readable schema.** The backend document specifies field-level JSON-compatible request and response contracts in tables and includes a complete delivery-response JSON example. The frontend document names operations and endpoint paths but defers full contract details to the backend document. The documented contract is therefore sufficient to type a client DTO layer, but it is not an OpenAPI artifact or a complete JSON example for every operation.

The main transport ambiguity is the request-level error envelope: the backend document defines `error.code`, `error.message`, and `error.fields`, plus field-path conventions, but does not show one complete JSON error body or explicitly state whether `error` is always nested at the top level. The frontend error mapping is consequently plan-able by vocabulary and paths, but should not be treated as fully locked until the envelope shape is confirmed.

#### Inconsistencies and readiness gaps

- The frontend specification says “no placeholder pages,” while the current routes still use `WarehousePage` placeholders and the existing reception page implements a different workflow.
- The frontend feature spec places reusable grid pieces under `common/grid/`; the data-grid pattern places the wrapper/editors under `common/components/`. This should be standardized before implementation.
- The architecture overview describes a future server-cache layer, while the feature specification explicitly requires page-local hooks and no global context and the package has no cache library. The feature plan can use local hooks, but the intended long-term convention should be confirmed.
- The frontend documentation is predominantly English, while current user-facing warehouse strings are Spanish. The UI language and whether this feature should follow existing Spanish copy need confirmation.
- The backend document describes a target/partial backend and explicitly must not be used as executable truth. Frontend integration can be planned against it, but real integration readiness remains unverified until the backend contract is implemented and exposed.

### Approaches

1. **Replace the legacy reception prototype with the documented feature module** — create the feature-local API/types/mappers/model/hooks and shared grid primitives, then implement reception, stock/detail, delivery, and routing/navigation in the documented sequence.
   - Pros: aligns the code with the authoritative docs; prevents legacy payload concepts from leaking into the new contract; supports isolated page state and explicit composition.
   - Cons: substantial replacement work; requires resolving shared-grid placement, error-envelope, language, and backend-readiness questions first.
   - Effort: High

2. **Incrementally extend the existing reception prototype** — adapt its current form/grid/hooks and add stock and delivery around it.
   - Pros: appears smaller initially; reuses existing `ReceptionPage` wiring.
   - Cons: current model, fields, endpoint, numeric representation, editable net weight, and error handling are incompatible with the target; likely creates migration complexity and hidden legacy behavior.
   - Effort: High, with higher rework risk

### Recommendation

Use Approach 1. Treat the existing reception implementation as a disposable prototype rather than a compatible foundation. Begin proposal/design only after resolving the explicit decisions below, then implement the feature in reviewable slices: foundation/shared grid and API contract, reception, stock/detail, delivery, and navigation/accessibility hardening. The complete scope is very likely to exceed the 400 changed-line review budget, so the single-PR default should be reconsidered or explicitly accepted as an exception.

### Clarification Required Before Proposal/Design

1. Should all new user-facing copy follow the existing Spanish UI, or should this feature use the English labels in the frontend specification?
2. Which shared-grid location is authoritative: `frontend/src/common/grid/` from the feature specification or `frontend/src/common/components/` from the data-grid pattern?
3. Should this feature use page-local hooks as specified, or is introducing a shared server-cache layer now required by the architecture target?
4. Confirm the exact top-level request-error JSON envelope, especially the nesting and shape of `error.fields`.
5. For successful delivery rows, should the UI make them read-only, remove them, or let the operator choose? The specification permits both read-only and removable behavior.
6. Should the legacy `/warehouse/reception` route be replaced/redirected to `/warehouse/bales/reception`, or remain as a separate future capability?
7. Is delivery’s documented operational maximum of 50 rows a frontend-enforced limit, a backend-only safeguard, or both?
8. Given the likely size, should implementation be split into chained/review slices despite the `single-pr-default` strategy, or is a deliberate over-400-line single PR acceptable?

### Risks

- **High review-size risk:** three pages, shared grid infrastructure, decimal arithmetic, transport mapping, accessibility, and route/navigation work will likely exceed 400 authored changed lines.
- **Contract integration risk:** backend documentation is target-state only; endpoint availability, exact error envelope, and OpenAPI serialization remain unverified.
- **Legacy collision risk:** the current reception route and types encode a different business model and could be accidentally reused.
- **Decimal correctness risk:** current rows use numbers, while the target requires string-preserving decimal arithmetic without `parseFloat` or rounding.
- **UX ambiguity risk:** language, successful-row handling, error envelope, shared-grid placement, and route migration are not fully decided.
- **Testing risk:** no frontend test framework is configured; quality gates currently provide build/lint only, leaving interaction and accessibility behavior to manual validation.

### Relevant Installed Skills for Later Phases

- `mantine-form` — reception header, stock filters, lookup form, and date validation.
- `vercel-composition-patterns` — explicit page/section composition and avoiding boolean-heavy grid/form components.
- `ui-ux-designer` — operational grid UX, responsive behavior, accessibility, loading/error/empty states, and focus flows.
- `playwright-cli` — manual browser workflow validation if browser automation is desired; it does not replace a configured frontend test runner.
- `cognitive-doc-design` — proposal/design/task artifacts and review-oriented documentation.
- `sdd-propose`, `sdd-spec`, `sdd-design`, `sdd-tasks`, `sdd-apply`, and `sdd-verify` — subsequent SDD phases.

The `supabase` and `supabase-postgres-best-practices` skills are not needed for this frontend-only exploration; backend/database work is out of scope.

### Ready for Proposal

**No, not yet.** The documentation and frontend provide enough context to understand the target and estimate the work, but proposal/design should wait for the eight decisions above—especially UI language, shared-grid/state conventions, error-envelope shape, route migration, and the review-size strategy. Once clarified, the feature is technically plan-able without inspecting backend source code.
