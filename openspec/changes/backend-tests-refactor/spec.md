# Delta for Backend Test Structure

## ADDED Requirements

### Requirement: Context-First Unit Test Topology

The unit suite MUST use context-first, layer-second Python packages, retaining a layer only where it expresses a test contract. Every package MUST contain `__init__.py`; test files MUST use `test_{name}.py` and `snake_case` names.

```text
backend/tests/
  __init__.py
  support/{__init__.py,builders.py,doubles.py,http_payloads.py,values.py}
  warehouse/{__init__.py,domain/{__init__.py,test_core_contracts.py},
    application/{__init__.py,test_registration.py},ports/{__init__.py},
    adapters/{__init__.py,test_mappers.py,test_repositories.py,test_transaction.py},
    api/{__init__.py,test_openapi.py,test_registration_endpoint.py},
    runtime/{__init__.py,test_composition.py,test_database_resources.py,test_settings.py}}
  access/{__init__.py,domain/{__init__.py,test_access_domain.py,test_role_presets.py},
    application/{__init__.py,test_access_application.py,test_access_impact_previews.py},
    adapters/{__init__.py,test_access_provisioning_adapter.py},
    api/{__init__.py,test_access_http_authorization.py},runtime/{__init__.py},support/{__init__.py}}
  auth/{__init__.py,domain/{__init__.py,test_auth_domain.py},
    application/{__init__.py,test_auth_application.py,test_auth_audit_login_events.py},
    adapters/{__init__.py,test_auth_adapter_provider.py,test_auth_jwt_validator.py},
    api/{__init__.py,test_auth_admin_authorization.py,test_auth_admin_endpoints.py,test_auth_endpoints.py},
    runtime/{__init__.py,test_auth_pipeline.py,test_bootstrap_command.py},support/{__init__.py}}
```

`yarn_production/` and `batch_processing/` MUST be created only when their respective context gains tests. Each MUST follow this same layout. A test MUST live in its owning context and most specific applicable layer; test splitting MUST preserve cohesive behavior rather than mirror every source file.

#### Scenario: Root module migration
- GIVEN `test_auth_pipeline.py` is a root unit-test module
- WHEN its Authentication runtime slice is migrated
- THEN it is discovered as `backend.tests.auth.runtime.test_auth_pipeline`
- AND its assertions remain unchanged in intent.

### Requirement: Verifiable Slice Migration

Each context/layer migration MUST be a separately verifiable slice. Before a slice is accepted, full discovery and that slice's context-qualified focused command MUST pass. Globally, discovery MUST report 252 passing unit tests with no behavior change.

#### Scenario: Context-qualified focused route
- GIVEN Warehouse core-contract tests have moved to `warehouse/domain`
- WHEN the documented focused module command is run
- THEN it targets `backend.tests.warehouse.domain.test_core_contracts`
- AND class or method suffixes remain supported.

### Requirement: Shared Support Admission

`backend.tests.support` MUST contain only context-neutral builders, values, HTTP payloads, and doubles whose tested protocol and state semantics are identical. Repository fakes, clocks, identity providers, and scenario builders MUST remain context-local until equivalence is demonstrated.

#### Scenario: Equivalent fake consolidation
- GIVEN two context-local doubles expose the same tested protocol and state transitions
- WHEN their equivalence is demonstrated
- THEN one shared double MAY replace them
- AND no consumer loses a method or semantic assertion.

### Requirement: Discovery and Compatibility Contract

`uv run --locked --package backend python -m unittest discover -s backend/tests -v` MUST remain the unit discovery command. Documentation MUST use context-qualified dotted paths. Existing absolute `backend.tests...` imports MUST remain absolute after relocation. `backend/integration_tests/` MUST remain unchanged.

#### Scenario: Discovery regression prevention
- GIVEN all migrated packages are present
- WHEN the full unit discovery command runs
- THEN all 252 tests pass
- AND no integration test or production module is changed.

### Requirement: Refactor Boundaries and Acceptance

The refactor MUST NOT change production behavior, RequestPipeline wiring or removal, the Starlette/httpx warning, or the PGRST106 issue. Per-slice acceptance requires unchanged assertions, successful full discovery, and a successful focused command. Global acceptance requires the target topology, documented focused paths, support-rule compliance, 252 passing tests, and an untouched integration suite.
