# Warehouse Bale Registration Authorization Specification

## Purpose

Require a server-derived Access decision before the single selected Warehouse write operation.

## Requirements

### Requirement: Protected Bale Registration

The system MUST protect only `POST /api/v1/warehouse/bales` with the server-derived exact requirement `write + warehouse.raw_materials`. It MUST resolve trusted identity and authorize before invoking business mapping, validation, or mutation. A successful decision MUST preserve the existing registration contract. No other Warehouse endpoint is protected by this capability.

#### Scenario: Authorized registration

- GIVEN a trusted subject with active exact `write + warehouse.raw_materials` permission or global administration
- WHEN it posts a valid bale-registration request
- THEN the existing registration operation executes and returns its normal success result

#### Scenario: Denial before mutation

- GIVEN a missing, inactive, or unauthorized identity
- WHEN it posts a bale-registration request
- THEN it receives `401` for unresolved identity or generic `403 access_denied` otherwise
- AND no Warehouse business mutation is attempted

### Requirement: Authorization Boundary Integrity

The resource scope and action MUST be derived by the server and MUST NOT be accepted from request data, headers, roles, or client scopes. Warehouse MUST consume only a narrow authorization decision and MUST NOT own Access policy or persistence behavior.

#### Scenario: Client-supplied authority is ignored

- GIVEN a request that supplies roles, scopes, or an alternate action
- WHEN it posts bale registration without the server-derived permission
- THEN authorization denies it without revealing Access state

#### Scenario: Unaffected endpoints

- GIVEN a request to Warehouse stock, detail, or delivery endpoints
- WHEN this capability is deployed
- THEN their authorization behavior is unchanged by this specification

## Out of Scope

Authentication validation, Supabase Auth, frontend changes, other protected resources, and package installation are excluded; installations MUST be user-executed. Local migration reset is verification-only.
