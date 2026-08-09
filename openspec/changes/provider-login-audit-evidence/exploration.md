## Exploration: provider-login-audit-evidence

### Current State
The Authentication PRD is normative. BR33 requires successful and failed login,
logout, expiration, and administrative session termination to remain traceable by
identity, date, and time; BR21 requires generic login denial; and AC19 requires
security history to identify affected accounts and administrators without exposing
secrets.

The backend specification is the implementation authority for this delta. It
defines two authoritative evidence sources: provider-observed evidence in
Supabase Auth and application-owned evidence in `authentication_audits`. Section
12.1 requires server-only reading of redacted `auth.audit_log_entries`, while
section 16 requires `GET /api/v1/auth/audits` to merge both sources, identify the
source of every item, remain provider-neutral, and never duplicate provider rows
into `authentication_audits`.

The current backend only queries `public.authentication_audits`. `ListAudits`
accepts a fixed internal limit and delegates to `AuthAuditRepository.list_recent`;
the HTTP response omits source, actor, reason, provider-session correlation, and
redacted details. The endpoint is administrator-authorized, but it is not yet a
cross-source paginated read model. `record_login_outcome` is an unwired C5 write
path and must not be used to duplicate provider login evidence.

The frontend specification is compatible: it consumes the same endpoint and
already separates provider concerns from backend audit data. No frontend code or
implementation work is needed for this change.

Supabase documentation confirms that Auth audit logs cover login, logout, token
refresh, and credential-related events, and that database persistence is optional;
the September 2025 changelog explicitly documents the setting that can disable
database writes while retaining Auth logs elsewhere. Therefore database-backed
evidence is available only when that provider setting is enabled.

Read-only local discovery via `pnpm supabase db query --local` found the current
`auth.audit_log_entries` shape to be `id`, `instance_id`, `payload` (JSON),
`created_at`, and `ip_address`. The observed payload contains `action`,
`log_type`, and `traits`; local data included `login`, `user_signedup`, and
`user_modified`. In the local login rows, `traits` did not contain `user_id`, so
failed-login correlation to an application account must remain nullable and the
adapter must not infer identity from email or error text. Local privileges also
showed `service_role` does not have direct SQL `SELECT` on this auth table;
section 12.1's restricted PostgreSQL connection or equivalently restricted
server-side function is therefore a real deployment concern, not an assumption.

### Affected Areas
- `backend/src/auth/ports/identity_provider.py` — extend the existing provider boundary with a provider-neutral audit evidence DTO and read operation, if the implementation keeps provider session and provider evidence in one cohesive port.
- `backend/src/auth/adapters/identity_provider/admin_client.py` — read `auth.audit_log_entries` through a server-only, least-privileged mechanism; map only allow-listed fields and redact IP, user agent, payload traits, and provider-specific details unless explicitly required by the response contract.
- `backend/src/auth/ports/audit_repository.py` and `backend/src/auth/adapters/persistence/audit_repository.py` — preserve application-owned audit reads while distinguishing them from provider evidence; no provider rows should be written here.
- `backend/src/auth/application/list_audits.py` — compose the two authoritative sources, apply stable ordering and a bounded cross-source page/limit, and return provider-neutral read-model entries.
- `backend/src/auth/adapters/http/models.py` and `backend/src/auth/adapters/http/admin_router.py` — add the source identifier and the smallest redacted, provider-neutral response fields required by the backend contract; retain administrator authorization.
- `backend/src/bootstrap/auth_dependency.py` — wire the provider evidence reader into the audit query without changing the frontend login path or unrelated Authentication composition.
- `backend/tests/test_auth_adapter_provider.py`, `backend/tests/test_auth_application.py`, and auth API tests — cover provider mapping, source-tagged merge/order, redaction, authorization, and empty/partial identity correlation.
- `supabase/config.toml` and deployment configuration — verify, but do not change speculatively, that database audit-log persistence is enabled and that the backend can use the restricted read mechanism.
- `openspec/changes/access-control-completion/specs/access-control-administration/spec.md` — existing C5 wording conflicts with the authoritative backend design and should be corrected in a later proposal/spec delta, not implemented as duplicate writes in this change.

### Approaches
1. **Extend the existing identity-provider port** — add a provider-neutral audit-read contract beside the already existing provider session lookup, then compose it with the application audit repository in `ListAudits`.
   - Pros: smallest boundary change; provider sessions and provider evidence already belong to the same external-provider responsibility; avoids an abstraction with no demonstrated pressure; preserves the existing composition root shape.
   - Cons: the concrete adapter needs a separate restricted SQL/function access path because the current service-role client is not sufficient for direct local SQL access; the port grows but remains cohesive.
   - Effort: Medium

2. **Create a dedicated provider-audit port and adapter** — isolate provider audit evidence behind a new read-only port and compose it with the application repository.
   - Pros: makes the read-only evidence dependency explicit and allows independent connection/configuration testing.
   - Cons: adds a new abstraction and composition path for one current consumer; increases wiring and configuration surface without demonstrated reuse or separate ownership pressure.
   - Effort: Medium

### Recommendation
Proceed with Option A using the existing identity-provider boundary, adding only a
provider-neutral audit evidence read contract. The existing port already owns
server-side provider administration and provider session state, and the backend
specification explicitly groups provider-owned session and audit reads behind the
identity-provider adapter. Do not add a dedicated port unless implementation
verification shows that the restricted database/function access path has an
independent lifecycle or will be reused outside Authentication.

The smallest coherent implementation is additive: read provider rows without
persisting them, normalize only supported actions into provider-neutral event
types/outcomes, merge them with application audits by occurrence time, identify
each row as `provider` or `application`, and redact all non-allow-listed payload
data. Preserve nullable account identity for failed or otherwise uncorrelated
provider events. Keep the existing direct frontend-to-Supabase login flow, webhook
ingestion, backend login endpoint, frontend implementation, logout wiring changes,
and unrelated Authentication completion out of scope.

No migration is currently justified. The provider table is provider-owned and the
application audit schema already supports the existing application events. A
configuration change is only justified if the current environment has provider
database audit persistence disabled or lacks the restricted server-side read path;
that must be verified during design/implementation rather than guessed here.

### Risks
- Supabase database audit persistence is optional; disabling it creates an evidence gap for this database-backed endpoint even though provider logs remain available elsewhere.
- The provider payload is JSON and its event shape can vary by Supabase/Auth version; mapping must be allow-listed, version-aware, and tested against the current local shape without exposing raw payloads.
- Failed login rows may not identify a user, so the API must not require an affected application account or reveal account existence.
- Cross-source pagination and equal timestamps need deterministic ordering and must not duplicate the same provider event or application audit.
- A server-role client is not proof of direct `auth.audit_log_entries` SQL access; deployment must provide a least-privileged restricted connection or server-side function as specified by §12.1.
- Existing C5 tests and the OpenSpec requirement describe duplicate application-owned login writes; they should be aligned before implementation, but changing that planning artifact is separate from provider read/merge behavior.

### Ready for Proposal
Yes. The proposal should state that this is a backend-only, additive Option A
change: expose merged provider/application evidence through the existing
administrator endpoint, source-tag every item, redact provider data, add focused
tests, and make no webhook, login-endpoint, frontend, migration, or Option C
logout changes. The design phase should first settle the restricted provider read
mechanism and the exact bounded pagination/response DTO.
