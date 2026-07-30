from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from warehouse.bales.domain.bale import Bale


@runtime_checkable
class BaleRepository(Protocol):
    """Persistence contract for bale storage operations.

    Implementations operate within the current transaction context.
    """

    def add_all(self, bales: Sequence[Bale]) -> None: ...

    def find_for_delivery(self, shipment_number: str, bale_number: str) -> Bale | None:
        """Look up a bale by its business identity (shipment_number + bale_number).

        Joins raw_material_bales with raw_material_batches on the normalized
        (uppercased) shipment_number and bale_number. Returns the domain Bale
        entity or None if no match exists.
        """
        ...

    def update_delivery(self, bale: Bale) -> bool:
        """Persist a bale's delivery transition using a conditional update.

        Executes UPDATE ... WHERE status = 'in_warehouse' to ensure
        concurrency safety. Returns True if the row was affected (transition
        succeeded), False otherwise (already delivered by a concurrent request).
        """
        ...
