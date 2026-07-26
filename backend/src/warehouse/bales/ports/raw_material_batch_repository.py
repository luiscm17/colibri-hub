from typing import Protocol, runtime_checkable

from warehouse.bales.domain.raw_material_batch import RawMaterialBatch


@runtime_checkable
class RawMaterialBatchRepository(Protocol):
    """Persistence contract for registering a raw-material batch.
    
    Implementations add the batch header within the current transaction context.
    """
    
    def add(self, batch: RawMaterialBatch) -> None: ...
