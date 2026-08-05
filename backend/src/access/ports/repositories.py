"""Backward-compatible re-exports from split port modules.

Each protocol now lives in its own file under access/ports/:
- users.py: AccessUserRepository
- roles.py: RoleRepository
- assignments.py: AssignmentRepository
- scopes.py: ScopeRepository, ScopeDefinitionRegistry
- audit.py: AccessAuditRepository

This file re-exports for existing consumers. New code should import
directly from the specific module.
"""

from access.ports.audit import AccessAuditRepository as AccessAuditRepository
from access.ports.roles import RoleRepository as RoleRepository
from access.ports.scopes import ScopeDefinitionRegistry as ScopeDefinitionRegistry
from access.ports.scopes import ScopeRepository as ScopeRepository
from access.ports.users import AccessUserRepository as AccessUserRepository
