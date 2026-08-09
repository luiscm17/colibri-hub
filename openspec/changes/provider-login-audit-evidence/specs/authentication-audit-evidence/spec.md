# Authentication Audit Evidence Specification

## Purpose

Define the administrator-facing Authentication audit history that combines unchanged application-owned records with safe, provider-observed successful password-login evidence.

## Scope and Known Gap

This slice advances BR33 only partially. Failed password-login traceability remains unresolved: this specification MUST NOT infer `login_failed`, treat the gap as satisfied, or redefine the normative PRD. `backend/docs/features/authentication.md` §16 requires a later correction and is not changed by this slice.

## Requirements

### Requirement: Unified Authentication Audit History

`GET /api/v1/auth/audits` MUST return an administrator-authorized, source-tagged page combining applicable application audits with the provider snapshot visible to that request. Items MUST use deterministic chronological order and an opaque cursor over the combined application evidence and that visible snapshot; this cursor MUST NOT imply visibility into provider history outside that snapshot.

#### Scenario: Administrator receives a combined page

- GIVEN an authorized administrator and eligible evidence from both sources
- WHEN the administrator requests an audit page
- THEN the response contains eligible records from the application and visible provider snapshot
- AND every item identifies `source` as `application` or `provider`

#### Scenario: Cursor is deterministic within visible evidence

- GIVEN a combined response with additional eligible visible evidence
- WHEN the endpoint emits or accepts a valid continuation cursor
- THEN ordering and cursor selection use one deterministic combined sequence
- AND the cursor does not assert complete provider history or retention

#### Scenario: Cursor is malformed

- GIVEN an authorized administrator and a malformed or unsupported cursor
- WHEN the administrator requests the audit history
- THEN the endpoint returns the established `422` validation response

### Requirement: Bounded Provider Success Snapshot

The provider contribution MUST be a bounded recent snapshot of available successful password-login evidence returned by the Supabase Admin Audit API. It MUST NOT promise provider historical completeness, retention duration, provider-side keyset pagination, a complete candidate set, or attested equal-timestamp tie completeness. Callers MUST NOT interpret this endpoint as a complete forensic archive.

#### Scenario: Available recent success is included

- GIVEN an eligible successful password-login entry is available in the provider snapshot
- WHEN the audit history is requested
- THEN it is eligible for the source-tagged combined response

#### Scenario: Older provider evidence is unavailable

- GIVEN a provider entry is absent from the snapshot due to provider availability or retention
- WHEN the audit history is requested
- THEN the response makes no claim that the entry was absent from provider history

### Requirement: Provider Success Evidence Scope and Ownership

The provider contribution MUST map only supported successful password-login evidence to `event_type: login_succeeded`. It MUST NOT return `login_failed`, copy, synthesize, or duplicate provider rows in `authentication_audits`; application-owned audits MUST remain unchanged.

#### Scenario: Successful provider login appears once

- GIVEN a supported provider-observed successful password login
- WHEN the audit history is requested
- THEN it appears at most once as `source: provider` and `event_type: login_succeeded`
- AND no duplicate application audit is created

#### Scenario: Unsupported provider events are excluded

- GIVEN provider evidence for failed validation, refresh, logout, or credential operations
- WHEN the audit history is requested
- THEN none of those events are returned by this slice

### Requirement: Safe Provider Evidence Projection

Provider items MUST use an explicit allow-list of provider-neutral fields and MUST redact credentials, tokens, authorization headers, cookies, raw payloads, provider secrets, and unsafe identifiers. `affected_account_id` MAY be null when safe UUID-based correlation is unavailable; identity text MUST NOT infer it.

#### Scenario: Correlated success is safely represented

- GIVEN a successful provider login safely correlated to an Authentication account
- WHEN it is returned in audit history
- THEN it includes only the allowed account reference and safe event metadata
- AND it exposes no prohibited provider data

#### Scenario: Uncorrelated success remains redacted

- GIVEN a successful provider login without safe UUID-based correlation
- WHEN it is returned in audit history
- THEN `affected_account_id` is absent or null
- AND no email, identifier text, or raw provider payload is returned

### Requirement: Atomic Provider Failure

Provider transport, authorization, malformed response, or invalid required provider fields MUST return `503 authentication_provider_unavailable`. The endpoint MUST NOT return a partial application-only or provider-only page for any such failure.

#### Scenario: Provider snapshot cannot be safely read

- GIVEN an authorized caller and a provider transport, authorization, malformed-response, or required-field failure
- WHEN the caller requests the audit history
- THEN the endpoint returns `503 authentication_provider_unavailable`
- AND it returns no partial audit page

### Requirement: First-Slice Boundary and Verification

This capability MUST NOT add direct PostgreSQL Auth-schema reads, grants, RPCs, migrations, webhooks, Log Drains, a backend login endpoint, frontend behavior, Option C, provider changes, provider logout, refresh, or credential-operation evidence. Local verification MAY use synthetic data only and MUST use root `pnpm supabase <command>` commands after discovery.

#### Scenario: Synthetic local verification

- GIVEN a local verification environment requiring reset
- WHEN integration evidence is prepared
- THEN only synthetic data is used
- AND no excluded integration or persistence mechanism is introduced
