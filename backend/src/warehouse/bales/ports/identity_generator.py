from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class IdentityGenerator(Protocol):
    def next_id(self) -> UUID: ...
