from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class IdentityGenerator(Protocol):
    """Contract for generating unique technical identities.
    
    Implementations provide UUID-based identities for domain entities.
    """
    
    def next_id(self) -> UUID: ...
