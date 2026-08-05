"""Access Control ports — protocol definitions for infrastructure adapters.

Per hexagonal architecture: ports define WHAT the domain/application needs,
adapters (in infrastructure) implement HOW.
"""

from access.ports.assignments import AssignmentRepository as AssignmentRepository
from access.ports.clock import ClockPort as ClockPort
from access.ports.identity import IdentityPort as IdentityPort
from access.ports.repositories import (
    AccessAuditRepository as AccessAuditRepository,
)
from access.ports.repositories import (
    AccessUserRepository as AccessUserRepository,
)
from access.ports.repositories import (
    RoleRepository as RoleRepository,
)
from access.ports.repositories import (
    ScopeDefinitionRegistry as ScopeDefinitionRegistry,
)
from access.ports.repositories import (
    ScopeRepository as ScopeRepository,
)
from access.ports.transaction import TransactionPort as TransactionPort
