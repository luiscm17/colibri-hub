# Proposal: Provider Login Audit Evidence

## Intent

Make `GET /api/v1/auth/audits` an administrator-authorized security-history read that merges existing application audits with provider-observed successful password-login evidence. Results remain source-tagged, redacted, and non-duplicated.

## Scope

### In Scope
- Read only provider-observed successful password-login evidence through the server-only Admin Audit API.
- Return a redacted, provider-neutral, source-tagged merge with application audits; never duplicate provider rows into `authentication_audits`.
- Preserve absent `affected_account_id` for uncorrelated successes and fail the combined endpoint with `503 authentication_provider_unavailable` when provider evidence cannot be read.
- Add focused merge, authorization, redaction, ordering, and synthetic local integration coverage.

### Out of Scope
- Failed password-login evidence and the provider/source solution required to obtain it; this is an explicit follow-up.
- Log Drains, webhooks, a backend login endpoint, frontend work, schema migration, Option C, and provider changes.
- Refresh, provider logout, credential-operation evidence, and unrelated Authentication completion.
- Correcting historical C5 planning/tests in this delivery.

## Business Impact and Compliance

This slice improves administrator traceability with safe provider-observed login success evidence while retaining application audits. It advances, but does not complete, BR33: failed password-login traceability remains unmet because current Supabase Auth does not persist failed password validation attempts in its audit evidence. The normative PRD remains unchanged.

## Capabilities

### New Capabilities
- `authentication-audit-evidence`: Provider-neutral, redacted, cross-source Authentication audit history.

### Modified Capabilities
None. No main OpenSpec capabilities currently exist.

## Approach

Use Option A: extend the existing identity-provider boundary with the smallest provider-neutral audit-read contract, then compose it with application audit reads in `ListAudits`. Read the supported server-only Admin Audit API; allow-list mapped fields, use deterministic bounded ordering, and keep provider-specific payloads private. No migration is proposed unless implementation evidence makes one unavoidable.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `backend/src/auth/ports/identity_provider.py` | Modified | Provider audit evidence read contract. |
| `backend/src/auth/application/list_audits.py` | Modified | Source-tagged merged read model. |
| `backend/src/auth/adapters/identity_provider/admin_client.py` | Modified | Restricted, redacted provider evidence mapping. |
| `backend/src/auth/adapters/http/` | Modified | Endpoint response and stable safe failure. |
| `backend/tests/`, `backend/integration_tests/` | Modified | Focused unit/API/local integration proof. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Provider audit availability or retention is insufficient | Med | Confirm configuration and retention; fail closed with 503 when unreadable. |
| Provider evidence has limited safe correlation | High | Keep account identity nullable; never infer from identity text. |
| Failed password attempts have no provider audit source | High | Defer evidence-source selection to an explicitly approved follow-up. |
| Old C5 artifacts conflict with Option A | Med | Treat as follow-up planning alignment, not duplicate writes. |

## Rollback Plan

Revert the additive provider-read, merge, and response changes together, restoring the existing application-audit-only endpoint. Do not alter provider-owned tables or persist copied provider rows.

## Dependencies

- Provider database audit persistence, retention, and server-only Admin Audit API availability.
- Local Supabase may be reset with confirmed CLI syntax: `pnpm supabase db reset --local --no-seed`.

## Success Criteria

- [ ] Administrators receive redacted application audits and provider-observed successful password-login evidence, each with a source.
- [ ] Each supported provider success appears once as `source: provider`; no provider evidence is duplicated into application audits.
- [ ] Provider evidence exposes no raw payload, credentials, tokens, or inferred identity; uncorrelated successes have no account identifier.
- [ ] Provider-read failure returns only `503 authentication_provider_unavailable`, never partial history.
- [ ] Synthetic local integration proof passes after `pnpm supabase db reset --local --no-seed` when the provider evidence path is available.
