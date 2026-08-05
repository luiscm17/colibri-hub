"""Backward-compatible re-exports from split adapter modules.

Each adapter now lives in its own file under access/adapters/persistence/:
- user_repository.py: AccessUserRepositoryAdapter
- role_repository.py: RoleRepositoryAdapter
- assignment_repository.py: AssignmentRepositoryAdapter
- scope_repository.py: ScopeRepositoryAdapter, ScopeDefinitionRegistryAdapter
- audit_repository.py: AccessAuditRepositoryAdapter

This file re-exports for existing consumers. New code should import
directly from the specific module.
"""

from access.adapters.persistence.assignment_repository import (
    AssignmentRepositoryAdapter as AssignmentRepositoryAdapter,
)
from access.adapters.persistence.audit_repository import (
    AccessAuditRepositoryAdapter as AccessAuditRepositoryAdapter,
)
from access.adapters.persistence.role_repository import (
    RoleRepositoryAdapter as RoleRepositoryAdapter,
)
from access.adapters.persistence.scope_repository import (
    ScopeDefinitionRegistryAdapter as ScopeDefinitionRegistryAdapter,
)
from access.adapters.persistence.scope_repository import (
    ScopeRepositoryAdapter as ScopeRepositoryAdapter,
)
from access.adapters.persistence.user_repository import (
    AccessUserRepositoryAdapter as AccessUserRepositoryAdapter,
)
