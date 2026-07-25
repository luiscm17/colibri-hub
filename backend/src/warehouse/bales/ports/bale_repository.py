from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from warehouse.bales.domain.bale import Bale


@runtime_checkable
class BaleRepository(Protocol):
    def add_all(self, bales: Sequence[Bale]) -> None: ...
