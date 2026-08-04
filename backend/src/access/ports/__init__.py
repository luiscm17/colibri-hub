"""Access Control ports — protocol definitions for infrastructure adapters.

Per hexagonal architecture: ports define WHAT the domain/application needs,
adapters (in infrastructure) implement HOW.
"""

from access.ports.clock import ClockPort as ClockPort
from access.ports.identity import IdentityPort as IdentityPort
from access.ports.repositories import (
    AccessAuditRepository as AccessAuditRepository,
    AccessUserRepository as AccessUserRepository,
    RoleRepository as RoleRepository,
    ScopeDefinitionRegistry as ScopeDefinitionRegistry,
    ScopeRepository as ScopeRepository,
)
from access.ports.transaction import TransactionPort as TransactionPort
