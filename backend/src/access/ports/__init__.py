"""Access Control ports — protocol definitions for infrastructure adapters.

Per hexagonal architecture: ports define WHAT the domain/application needs,
adapters (in infrastructure) implement HOW.

Each port has its own module file. This package re-exports all protocols
for convenient access: `from access.ports import AccessUserRepository`.
"""

from access.ports.assignments import AssignmentRepository as AssignmentRepository
from access.ports.audit import AccessAuditRepository as AccessAuditRepository
from access.ports.clock import ClockPort as ClockPort
from access.ports.identity import IdentityPort as IdentityPort
from access.ports.roles import RoleRepository as RoleRepository
from access.ports.scopes import ScopeDefinitionRegistry as ScopeDefinitionRegistry
from access.ports.scopes import ScopeRepository as ScopeRepository
from access.ports.transaction import TransactionPort as TransactionPort
from access.ports.users import AccessUserRepository as AccessUserRepository
