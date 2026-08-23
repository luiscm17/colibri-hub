---
document_type: technical-spec
status: draft
scope: authentication
authority: explanatory
owner: frontend
---

# Technical Specification - Frontend Authentication

> **Normative PRDs:** [Authentication](../../../docs/prd/auth.md) and
> [Access Control](../../../docs/prd/access-control.md)
>
> The PRDs are authoritative for business behavior. This specification defines
> the frontend consequences of those rules and the implemented contracts it
> consumes.

## 1. Purpose and boundary

The Authentication frontend establishes an observable application identity from
a provider-owned browser session, validates the corresponding Colibri Hub
account, enforces mandatory password replacement, ends local use of sessions,
and presents account administration. A provider session alone never admits
protected content: `GET /api/v1/auth/me` must first validate the application
account and state the next step.

Authentication owns entry, credentials, account state, and session UX. Access
Control separately owns profiles, roles, permissions, business scopes,
authorization bootstrap, and permitted destinations. Their unified System
Administrator workspace consumes both contracts without merging ownership.

Supabase browser Auth is the browser identity and session boundary because its
persisted sessions, automatic refresh, session events, and sign-out behavior
materially define browser continuity. The backend remains authoritative for
application account state, mandatory replacement,
administrative mutations, audit evidence, and every protected request. The
frontend neither validates tokens nor treats visibility or navigation as a
security boundary.

Implementation follows the [Frontend Architecture Overview](../architecture/overview.md).
Technology families are owned by the
[Technology Baseline](../../../docs/architecture/technology-baseline.md), exact
dependencies by repository manifests, styling by
[Frontend Styling](../../../docs/dev-guide/frontend-styling.md) and
[Visual Identity](../design-system/visual-identity.md), accessibility by the
[Accessibility Guidelines](../accessibility.md), and verification levels by the
[Frontend Testing Strategy](../testing/strategy.md).

## 2. Authentication state contract

### 2.1 States

Authentication state is exactly one of:

| State | Carries | Meaning |
| --- | --- | --- |
| `initializing` | none | Initial provider restoration and account validation are unresolved |
| `unauthenticated` | reason: `logged-out`, `expired`, or `denied` | No usable application session exists |
| `password-change-required` | account | The account is validated but only mandatory replacement, state inspection, and logout are available |
| `authenticated` | account with `next_step=load_access` | Authentication is eligible to hand off to Access |
| `unavailable` | retryable | Provider or backend availability prevents a trustworthy result |

The account model contains only the normalized non-secret account identity needed
for presentation: account identifier, organizational email, display name,
account status, and next step. Transport fields are validated and normalized at
the Authentication boundary. Provider users, sessions, tokens, token claims,
password flags, private metadata, roles, and permissions are not presentation
state.

Only `authenticated` may initiate Access bootstrap. `initializing`,
`password-change-required`, and `unavailable` expose no protected content.

### 2.2 Complete transitions

| Current condition and event | Required transition and observable result |
| --- | --- |
| Application starts | Enter `initializing`; expose neither prior account nor protected content |
| Restore finds no provider session | Enter `unauthenticated/logged-out` |
| Restore or login yields a provider session | Validate it through `/auth/me` before publishing an account |
| `/auth/me` returns `next_step=change_password` | Enter `password-change-required`; clear Access and allow only the restricted Authentication experience |
| `/auth/me` returns `next_step=load_access` | Enter `authenticated` and issue one semantic handoff to Access |
| Login credentials or account validation are denied | Clear the provider-owned browser session and sensitive state; enter `unauthenticated/denied` |
| Session expires, refresh becomes unrecoverable, or a protected request reports an ended session | Clear provider, Authentication, Access, and sensitive state; enter `unauthenticated/expired` and move to sign-in |
| Current account becomes disabled or reset and the backend denies its session | Apply the same ended-session outcome without waiting for a provider event |
| Provider or backend is unavailable during initial resolution | Enter `unavailable`; protected content remains absent |
| Provider or backend is unavailable after a validated state | Do not publish a different account or an unvalidated state; present non-destructive retry only where the existing state remains trustworthy, otherwise enter `unavailable` |
| Retry from `unavailable` with a current provider session | Revalidate `/auth/me`; publish only the latest matching result |
| Retry from `unavailable` without a provider session | Enter `unauthenticated/logged-out` |
| Password replacement returns `204` | Clear password fields and revalidate `/auth/me` using the existing session |
| Revalidation after replacement returns `load_access` | Enter `authenticated`; preserve the original session time-box and hand off once to Access |
| Provider invalidates the session during replacement | Clear all session-dependent state and enter `unauthenticated/expired` |
| Logout is requested from any session-bearing state | Perform the termination sequence in Section 3.4, then enter `unauthenticated/logged-out` |

### 2.3 Access handoff

Authentication supplies the exact semantic conditions consumed by the sibling
[Access specification](access-control.md):

| Authentication condition | Access consequence |
| --- | --- |
| Unresolved | `waiting-for-authentication`; do not request Access |
| Unauthenticated or ended | Clear prior Access, enter `waiting-for-authentication`, and do not request Access |
| Password change required | Clear prior Access, enter `waiting-for-authentication`, and expose no protected capability |
| Authenticated and eligible with `next_step=load_access` | Enter Access `loading` and bootstrap Access |
| Authentication unavailable | Enter Access `unavailable`; do not request Access |

Repeated provider events or equivalent account-validation results do not duplicate
Access bootstrap, destination selection, or navigation for the same relevant
session transition. Authentication communicates conditions and transitions, not
Access implementation topology.

## 3. Provider and session contract

### 3.1 Browser boundary

The browser receives only the public provider URL and public publishable key.
Administrative credentials and service-role secrets are prohibited from public
configuration and frontend artifacts. Unsupported link, recovery, registration,
and identity-provider flows remain unavailable.

The provider SDK exclusively owns browser session persistence, restoration,
access-token refresh, and local sign-out. The application creates no parallel
token store, session registry, session deadline, or persisted token copy. Backend
requests obtain the current access token through one centralized asynchronous
boundary; presentation never reads or receives it.

### 3.2 Event normalization and races

Provider restoration, login, refresh, and sign-out events are normalized into the
state transitions in Section 2. Exactly one authoritative `/auth/me` validation
may publish an account for each relevant session transition.

- A newer provider event invalidates pending validation for the prior session.
- A response may publish state only if it still belongs to the current provider
  session and latest validation attempt.
- Duplicate events for the same effective session state are deduplicated.
- A stale success cannot restore a signed-out, expired, replaced, or disabled
  account; a stale failure cannot overwrite a newer valid result.
- Navigation is a consequence of the published semantic state, not of a
  low-level provider callback.

Initial resolution has no protected snapshot to retain. A non-destructive retry
may retain clearly identified, still-trustworthy content while showing refresh
progress, but it must not present stale identity as newly validated. Changing
accounts clears or marks the previous account as non-current before any new
result, so one person's details never flash as another person's.

### 3.3 Time-box and backend denial

The session has a fixed maximum of eight hours from the login that created it.
Provider persistence and refresh own browser continuity; backend validation is
authoritative for whether a protected request remains usable. The frontend does
not calculate, restart, or extend the maximum. Mandatory password replacement
continues the original session for only its remaining time.

An Authentication `401` or equivalent ended-session outcome clears session-bound
state and returns to sign-in. A mutation is never automatically replayed after
refresh or reauthentication. Access denial is handled by Access and does not by
itself imply that Authentication ended.

### 3.4 Logout

Logout has this observable sequence:

1. While a token remains available, attempt `DELETE /api/v1/auth/session` so the
   backend can record and request termination of the current session.
2. Regardless of backend success, perform provider-owned local sign-out and clear
   its browser session state.
3. Clear token access, Authentication state, Access state, sensitive query data,
   secret drafts, and authorization-dependent drafts.
4. Navigate to the addressable sign-in destination as `logged-out`.

The sequence accepts one pending logout and is locally idempotent. Failure of the
backend request must not trap the user in the protected experience. The frontend
guarantees observable browser termination and clearing. It does not represent
`DELETE /api/v1/auth/session` as immediate access-token revocation: an already
issued provider JWT may remain technically valid until its expiry even after its
browser session is signed out. Provider sign-out scope beyond this browser is not
implied unless a supported administrative flow explicitly requests it.

## 4. Entry experience

### 4.1 Sign-in destination and return intent

Sign-in is addressable and may carry a validated return intent to a protected
destination. The intent contains no credentials or secret state. After successful
Authentication, Access resolves authorization before navigation:

- use the intended destination only when it is valid and permitted;
- otherwise use the first permitted destination;
- when no active Access is available, use the Access-owned blocked outcome; and
- never use return intent to bypass Access bootstrap or destination checks.

An already authenticated user entering sign-in follows the same Access-aware
destination resolution. A password-change-required user is sent only to the
mandatory replacement experience.

### 4.2 Login form and submission

The form contains organizational email, password, and one primary submit action.
Email identifies the username and exposes the corresponding autocomplete
purpose; password exposes current-password autocomplete. Submission validates
required input, shows progress, and blocks an identical duplicate request.

Provider credential denial and account denial produce the same generic message
without identifying whether the email exists, the password is wrong, the account
is disabled, or another entry condition failed. Provider technical details are
never rendered.

Only the latest submission may change state or present an error. Navigating away,
starting a newer submission, expiration, or logout abandons the prior result; its
late success or failure remains invisible.

### 4.3 Login draft lifecycle and focus

- Email may remain after a recoverable denial to support correction.
- Password clears after denial, navigation away, expiration, logout, or success.
- Neither value is persisted across reload, placed in a URL, or sent to logs or
  telemetry.
- Field validation is associated with its input; submission failure moves focus
  to the first actionable field or a generic result summary.
- The generic result is announced without including either submitted value.

## 5. Mandatory password replacement

### 5.1 Restricted experience

While `password-change-required`, the only available interactions are current
Authentication state inspection, mandatory password replacement, and logout.
Direct entry, history, or return intent cannot expose protected or Access
administration content.

The form contains current provisional password, new password, new-password
confirmation, safe password-policy feedback, and submit. It validates that the
confirmation matches and that current and new values differ before submission;
the backend remains authoritative for password policy and account transition.
Password visibility controls identify their target and expose current visible or
hidden state.

### 5.2 Completion and recovery

The frontend submits current and new passwords to
`POST /api/v1/auth/password-change`. A `204 No Content` success is consumed as
completion without parsing a body. It then clears all password values and
revalidates `/auth/me` with the existing provider session. Access starts only
after that response reports `next_step=load_access`.

The frontend never starts a replacement session or extends the original
eight-hour maximum. If the provider session is no longer valid, the outcome is
expiration and sign-in, not implicit relogin.

Only one identical replacement may be pending. Safe validation feedback points
to the affected field; provider or backend unavailability offers retry without
implying completion. Password values clear on success, navigation away, reload,
expiration, logout, account-state conflict, or any failure where retaining them
is unsafe. They are never persisted across navigation or reload.

Leaving or closing a dirty replacement interaction requires confirmation because
the user would lose entered secrets. Staying restores focus to the interaction;
leaving clears every password value. Successful completion or logout clears the
dirty and confirmation state.

## 6. HTTP capabilities consumed

### 6.1 Session and account state

| Capability | Method | Path | Success |
| --- | --- | --- | --- |
| Inspect Authentication state | `GET` | `/api/v1/auth/me` | `200` account and `change_password` or `load_access` next step |
| Replace provisional password | `POST` | `/api/v1/auth/password-change` | `204`, no body |
| Record and request session termination | `DELETE` | `/api/v1/auth/session` | `204`, no body |

Ordinary login, browser persistence, refresh, and local sign-out use the provider
browser boundary; there is no backend login endpoint.

### 6.2 Administration

| Capability | Method | Path | Success |
| --- | --- | --- | --- |
| List accounts | `GET` | `/api/v1/auth/accounts` | `200` complete account-summary collection |
| Provision account and Access | `POST` | `/api/v1/auth/accounts` | `201` non-secret account summary |
| Get account | `GET` | `/api/v1/auth/accounts/{account_id}` | `200` account detail |
| Reset password | `POST` | `/api/v1/auth/accounts/{account_id}/password-reset` | `204`, no body |
| Disable account | `POST` | `/api/v1/auth/accounts/{account_id}/disable` | `204`, no body |
| Enable account | `POST` | `/api/v1/auth/accounts/{account_id}/enable` | `204`, no body |
| Query Authentication audits | `GET` | `/api/v1/auth/audits` | `200` cursor page |

Exact transport fields, validation, and error envelopes belong to the backend
contract and OpenAPI. The frontend validates and normalizes complete responses,
supports stale-response rejection, and exposes observable account, collection,
audit, and mutation outcomes rather than raw transport objects.

## 7. Unified account administration

### 7.1 Information architecture

The System Administrator workspace requires the Access-owned `manage_access +
access_control` authorization defined by the sibling specification. Backend
authorization remains authoritative.

| Destination | Primary purpose | Observable relationships and transitions |
| --- | --- | --- |
| Accounts | Consult Authentication account summaries and start provisioning | Collection to addressable account detail or create; restores collection context on return |
| Account detail | Consult Authentication and related Access state and initiate lifecycle actions | Detail to reset, disable, or enable confirmation according to current state; Back returns to origin |
| Provision account | Establish one account, profile, and initial role set | Addressable create interaction; cancel returns to the originating Accounts context |
| Authentication History | Consult implemented Authentication evidence | Cursor collection; affected account may link to a permitted existing detail, but no audit detail is implied |

Reset, disable, and enable are reversible review interactions associated with the
current account; this contract does not prescribe whether they occupy a page or
another presentation surface. Direct entry and refresh resolve the addressed
account without depending on a mounted collection row.

Cancel or Back restores known Accounts collection context; otherwise it returns
to the default Accounts destination. If the account is stale, missing, or no
longer permitted, clear it as current and move to the nearest valid destination:
Accounts first, another permitted administration destination second, then the
general permitted application destination. History must not restore a denied or
different account as current.

### 7.2 Account collection

The implemented account list returns the complete summary collection and accepts
no search, status filter, sort, or pagination parameters. The frontend must not
present server-wide criteria or pagination that the contract does not support.
Any local search, filter, grouping, or ordering applies only to the loaded
collection and is identified as local presentation behavior.

The collection distinguishes initial loading, non-destructive refresh, no
accounts, no local matches, retryable failure, and loaded results. Only the latest
request may replace the collection. After a mutation, refresh affected account
and collection snapshots; a late pre-mutation response cannot overwrite them.

### 7.3 Authentication History

History accepts only the backend-issued `cursor`; it has no implemented event,
outcome, account, source, text, or date filter. The cursor is opaque and is used
only to request the next page. A changed initial query or refreshed history
invalidates later-page continuity rather than combining different snapshots.

Each entry presents only backend-issued metadata: audit identity, operation
correlation when present, event type, outcome, affected account when present,
occurrence time, and source. Source distinguishes `application` evidence from the
current `provider` evidence exposed by the backend. The frontend does not infer an
actor, reason, provider subject, completeness, retention period, failed-login
traceability, or unavailable evidence.

History distinguishes initial loading, no evidence, end of results, loading more,
retryable page failure, and loaded pages. Repeated load-more actions do not issue
duplicate requests. A stale cursor response cannot append to a refreshed chain,
duplicate an entry, reorder already established continuity, or replace a newer
result.

### 7.4 Provisioning

Provisioning is one atomic backend request containing:

- organizational email;
- display name;
- user code;
- provisional password and frontend confirmation;
- one or more active Access role codes; and
- administrative reason.

The administrator explicitly acknowledges organizational control of the email
and responsibility for communicating the provisional password outside Colibri
Hub. The system neither verifies nor administers the mailbox and never emails,
echoes, or displays the password after success.

Role selection consumes Access's backend-authorized eligible provisioning-roles
projection, not the general Access roles collection. The projection contains only
active eligible roles and no permission payload. The selector follows the
searchable multiple-selection semantics in
[Frontend Access Control](access-control.md#63-users-and-role-assignment); role
identity remains unambiguous and the complete non-empty set is submitted once.
Authentication does not duplicate role or permission semantics.

Incomplete or failed provisioning never presents a usable account or successful
Access. Recoverable errors preserve safe non-secret account and role input.
Password and confirmation clear on success, navigation, reload, expiration,
logout, duplicate-email resolution that changes identity context, and any failure
where retention is unsafe. Success clears the draft and presents only non-secret
account identity plus the external-communication reminder.

### 7.5 Account detail and lifecycle actions

Detail presents separate Authentication and Access sections. Authentication may
show account identity, organizational email, display name, user code, lifecycle
status, and version. Access supplies an account-addressed review projection with
profile state and assigned-role summaries under its own backend-authorized contract.
The frontend does not join Access data, resolve capabilities, or make authorization
decisions from this review. Provider subject, private metadata, credentials, password
flags, tokens, and credential history are never exposed. No email, display-name,
or user-code editing is offered because no implemented mutation supports it.

Every reset, disable, or enable uses `expected_version` from the latest account
detail and an administrative reason. Confirmation identifies the account,
requested transition, current state, consequences, and cancel/confirm actions.
It remains reversible until submission, exposes progress, and accepts only one
identical pending mutation.

| Action | Additional input and confirmation consequence |
| --- | --- |
| Reset password | New provisional password and confirmation; active sessions are requested to end, the account becomes awaiting password change, and the credential must be communicated outside the system |
| Disable | Explain that login is denied, sessions are requested to end, the Access profile is inactivated, and identity and history remain preserved |
| Enable | Review current Access profile state and assigned-role summaries, provide a new provisional password and confirmation, and explain that re-enablement may proceed with zero active assigned roles, grants no capability by implication, and remains blocked until mandatory replacement |

Password replacement and administrative password update do not by themselves
prove that every other provider session or already issued access token has been
revoked. The frontend presents the backend-coordinated account transition and
session-termination request, while applying the JWT-expiry limitation in Section
3.4 to any claim about immediate token invalidation.

The backend enforces account state and the last-operational-System-Administrator
invariant. The frontend may explain known effects but never predicts success from
client state. A `204` mutation success clears secrets and confirmation, then
reloads detail and affected collections before presenting the resulting state.

On version conflict, preserve safe draft input separately, clear passwords,
invalidate confirmation, load current detail for comparison, and require a new
confirmation with the new version. Never insert a fresh version into an old
pending action. State conflict follows the same reload and reassessment. Missing
detail clears the stale subject and returns to Accounts. Failure returns focus to
the result or first recovery action; cancel restores focus to the initiating
action when it remains available.

## 8. Draft and async contract

### 8.1 Draft lifecycle

| Event | Required result |
| --- | --- |
| Recoverable validation, network, or server failure | Preserve safe non-secret draft and reason; associate actionable feedback and offer retry where safe |
| Authorization change | Preserve safe input only long enough to explain and reevaluate; clear it before leaving a permitted administration boundary |
| Concurrency or account-state conflict | Keep safe proposal separate from newly loaded current state, clear secrets, invalidate confirmation, and require renewed review |
| Cancel, Back, account switch, or leave while dirty | Require discard confirmation for non-secret administrative work; staying restores focus |
| Successful mutation | Clear draft, secrets, confirmation, and pending state |
| Logout or expiration | Clear all secret, sensitive, and authorization-dependent drafts immediately |
| Reload | Do not restore drafts; load authoritative destination state |

Passwords additionally clear whenever Section 4.3, Section 5.2, or the relevant
administrative lifecycle requires it. No password draft survives navigation or
reload. Non-secret drafts have no cross-reload persistence by default and never
move from one account operation to another.

### 8.2 Loading, races, and performance

- Only the latest relevant response for the current session, account, collection,
  cursor chain, or mutation may update visible state.
- An abandoned request produces no visible stale error or success.
- Changing accounts clears or marks prior detail as non-current before loading;
  previous-account data never flashes as current.
- Initial loading and non-destructive refresh are observably distinct.
- An identical pending login, replacement, logout, or administration mutation
  cannot be submitted twice.
- Successful mutations invalidate older snapshots before refresh results may
  publish.
- Account-administration code and content are not required on the initial path
  for users without `manage_access + access_control`; entering a newly permitted
  destination may have its own loading state.

These are observable constraints, not prescriptions for request cancellation,
caching, rendering, state management, or code splitting.

### 8.3 Adopted technology consequences

React must receive provider events and asynchronous account validations as one
coherent external-session snapshot. Subscription cleanup must prevent abandoned
listeners from publishing, repeated equivalent events must not duplicate state
transitions, and stale validations must not publish obsolete identity, navigation,
or Access bootstrap. Account eligibility, next destination, and other values
derived from the current Authentication and Access snapshots are not maintained
as independent competing state. Deferred or transitional rendering may preserve
responsiveness, but never changes which request result is current or correct.

Mantine's higher-level form controls are preferred for ordinary Authentication
and account-administration inputs because they provide accessible labeling and
description structure. This capability still owns explicit labels, associated
errors, announcements, focus recovery, and password-control semantics; theme and
component defaults do not prove accessibility. A lower-level input is justified
only when the required interaction cannot be expressed by the higher-level
control and receives the missing semantics explicitly.

Privileged account administration is not required in the initial unauthenticated
React path or in the initial path of users without the administration grant.
Loading it later may introduce a distinct loading state, but must not alter route
authorization, stale-result rejection, or direct-navigation correctness.

## 9. Errors, security, and responsive behavior

### 9.1 Normalized outcomes

| Condition | Frontend outcome |
| --- | --- |
| Provider login denial or denied account validation | Generic entry denial; clear password |
| `authentication_required` | Consume ended-session behavior and return to sign-in |
| `password_change_required` | Clear Access and enter mandatory replacement |
| `access_denied` | Defer to Access without treating a valid Authentication session as ended |
| Duplicate Authentication email | Associate safe feedback with provisioning email |
| Missing account | Clear stale detail and return to the nearest valid destination |
| Authentication version or state conflict | Preserve safe input, clear secrets, reload current detail, and require new confirmation |
| Last System Administrator invariant | Keep safe context and explain why the action was rejected |
| Replacement password equals current or password is weak | Associate safe policy feedback without echoing either value |
| Required administrative reason is absent | Associate feedback with reason |
| Provider, network, or backend unavailable | Preserve safe non-secret state where valid and offer retry without implying success |

Technical provider messages, account-enumeration details, stack traces, SQL, raw
transport failures, and credential values are never presented.

### 9.2 Security

- No password, access token, refresh token, authorization header, provider secret,
  or credential response enters URLs, route state, general storage, logs,
  telemetry, analytics, audit presentation, or non-secret drafts.
- Provider persistence is the single browser token store; application state never
  duplicates token material.
- Backend account validation precedes protected rendering after restore and login.
- Access remains the separate authority for profile state, permissions, routes,
  and actions; Authentication never branches on role names.
- Browser state, return intent, visible controls, and locally retained account
  summaries establish neither identity nor authorization.
- Session end clears Authentication, Access, secret drafts, sensitive query data,
  and authorization-dependent state.

### 9.3 Responsive information priority

Viewport constraints may change density, not capability:

| Experience | Information that remains primary |
| --- | --- |
| Sign-in | Destination identity, email, password, generic result, and submit |
| Mandatory replacement | Restricted-session context, all password fields, policy feedback, logout, and submit |
| Accounts | Collection heading, account identity, account status, and available primary action |
| Account detail | Account identity, Authentication status, Access relationship, versioned action, and return path |
| Confirmation | Account, requested transition, consequences, reason, secret input when applicable, cancel, and confirm |
| Authentication History | Event, outcome, occurrence time, source, affected account relationship, and continuation state |

No critical Authentication or session-ending action is hidden solely because of
viewport size. Secondary metadata may use progressive disclosure without hiding
state, validation, consequences, or recovery needed for a safe decision.

## 10. Feature-specific accessibility

In addition to the transversal [Accessibility Guidelines](../accessibility.md):

- password visibility controls name the affected field and expose visible or
  hidden state;
- generic entry denial and announcements contain no submitted email, password,
  provider detail, or account-enumeration clue;
- field errors are associated with their inputs, while submission outcomes move
  focus to the first invalid field, result summary, or recovery action;
- expiration moves focus to a non-sensitive notice that explains sign-in as the
  next action;
- account status and pending lifecycle effects are expressed in text rather than
  color alone;
- confirmations identify the account and consequences, retain a reversible path,
  and restore focus to the initiating action when still valid;
- History exposes semantic relationships among event, outcome, time, source,
  affected account, and operation correlation without fabricating missing data;
- role selection in provisioning follows the selector accessibility semantics in
  the sibling Access specification; and
- secret-safe status announcements never repeat credential values.

## 11. Observable verification scenarios

Verification follows the [Frontend Testing Strategy](../testing/strategy.md).
The implementation must prove these observable contracts at justified levels.

### Authentication entry and session

- Initial restore distinguishes no session, password change required,
  authenticated eligibility, denial, and unavailability without protected-content
  flash.
- Restored and newly created provider sessions publish no account before the
  latest matching `/auth/me` succeeds.
- The exact state machine handles login, restore, account validation, retry,
  refresh failure, expiration, disablement, reset, provider outage, backend
  outage, and logout.
- Duplicate provider events and stale validations cannot republish prior state or
  duplicate Access bootstrap and navigation.
- Access receives exactly the semantic conditions in Section 2.3 and starts only
  for `next_step=load_access`.
- Login is addressable, validates return intent through Access, prevents duplicate
  submission, preserves email where safe, clears password, and presents generic
  denial with correct focus and announcement.
- Mandatory replacement isolates all protected content, validates confirmation
  and password difference, clears secrets safely, consumes `204` without a body,
  revalidates `/auth/me`, and preserves the original session maximum.
- Provider invalidation during replacement returns to sign-in rather than
  implying a renewed session.
- Dirty replacement departure is reversible and no password survives navigation,
  reload, expiration, logout, success, or unsafe failure.
- Logout attempts the backend request while authenticated, always signs out and
  clears browser state locally, clears Authentication and Access, and reaches
  sign-in even when the backend call fails.
- Expiration and ended-session denial clear sensitive state, receive focus, and
  never replay a mutation automatically.

### Account administration

- Accounts, addressable detail, provisioning, History, and lifecycle
  confirmations expose the relationships, return behavior, and nearest-valid
  recovery defined in Section 7.
- Account collection uses the implemented complete-list contract without
  promising server filters or pagination; local criteria are labeled, stale
  results are rejected, and empty differs from no local matches.
- History sends only opaque cursor continuation, exposes only implemented
  metadata and source distinction, preserves cursor-chain continuity, and
  distinguishes empty, loading-more, end, and retry states.
- Provisioning requires all account fields, confirmation, at least one active
  Access role, reason, and organizational-control acknowledgement; it submits one
  atomic request and never echoes or retains the provisional password after
  success.
- Recoverable provisioning failure preserves only safe draft data and never
  implies that partial account or Access configuration is usable.
- Detail separates Authentication and Access information and exposes no provider
  subject, private metadata, credential, token, password flag, or unsupported
  account editing.
- Reset, disable, and enable present their exact consequences, reason,
  `expected_version`, progress, duplicate prevention, last-administrator outcome,
  focus recovery, and post-success refresh.
- Enable requires Access profile-state and assigned-role-summary review plus a
  new confirmed provisional password; zero active assigned roles do not block
  re-enablement or imply a capability. Reset and enable result in awaiting
  password change; disable preserves identity and history while affecting login,
  sessions, and profile state.
- Version and state conflicts keep safe proposals separate, clear secrets, load
  current detail, and require a new confirmation; stale and missing accounts
  never remain current.
- Cross-cutting draft rules preserve safe work on recoverable errors, confirm
  dirty departure, isolate accounts, clear on success or session end, and do not
  promise reload persistence.

### Async, responsive, accessibility, and security

- Rapid session, account, cursor, and navigation changes allow only the latest
  relevant result to publish; abandoned requests remain invisible and prior
  account data never flashes as current.
- Initial loading and refresh remain distinct, and every identical pending
  mutation is accepted once.
- Users without account-management authorization do not require administration
  content on their initial application path.
- Narrow viewport presentation retains the primary information and critical
  actions in Section 9.3 without prescribing breakpoints.
- Password controls, generic denial, expiration, forms, confirmations, account
  status, History metadata, role selection, announcements, and focus satisfy
  Section 10 and the transversal accessibility contract.
- No secret or duplicate token state appears in URLs, storage, presentation,
  logs, telemetry, or stale drafts; backend account validation and separate Access
  authority remain mandatory.

## 12. Completion criteria

### Authentication entry and session

1. The exact Authentication states and transitions govern restore, login,
   validation, password replacement, retry, logout, expiration, and outage.
2. Provider-owned persistence and refresh are the only browser session mechanism;
   token access is centralized, asynchronous, and absent from presentation.
3. `/auth/me` validates every restored or newly authenticated session before
   protected content or Access bootstrap.
4. Race and deduplication rules prevent stale publication, duplicate Access
   bootstrap, and repeated navigation.
5. Login and mandatory replacement satisfy their return-intent, draft, focus,
   generic-denial, secret lifecycle, `204` revalidation, and fixed time-box
   contracts.
6. Logout always completes provider-local termination and frontend clearing while
   making no unsupported backend token-revocation guarantee.

### Account administration

1. Unified administration consumes Authentication account capabilities and the
   sibling Access role/profile contract without transferring ownership.
2. Account collection and History expose only implemented list, cursor, metadata,
   and source capabilities.
3. Provisioning is one complete request with organizational acknowledgement,
   write-only provisional credential, and one or more active Access roles.
4. Detail, reset, disable, and enable satisfy version, confirmation, invariant,
   lifecycle consequence, conflict recovery, focus, and secret-clearing contracts.
5. Navigation, drafts, async behavior, responsive adaptation, accessibility, and
   security satisfy Sections 7 through 10 without depending on a prescribed
   provider topology, component, state-management, form, cache, or verification
   implementation.
6. All observable verification scenarios pass against the implemented provider,
   backend, and Access contracts.
