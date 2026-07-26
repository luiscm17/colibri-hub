from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from warehouse.bales.domain.bale import Bale


@runtime_checkable
class BaleRepository(Protocol):
    """Persistence contract for batch-registering multiple bales.
    
    Implementations add all bales within the current transaction context.
    """
    
    def add_all(self, bales: Sequence[Bale]) -> None: ...
