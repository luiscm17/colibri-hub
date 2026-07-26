from dataclasses import dataclass

from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_status import BaleStatus
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.domain_errors import InvalidBaleStateTransitionError
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId


@dataclass(slots=True, init=False)
class Bale:
    """Independently identified raw-material unit with its own custody lifecycle.
    
    A bale is the raw-material unit received from suppliers. Each bale has
    independent technical identity and its own lifecycle, transitioning from
    IN_WAREHOUSE to DELIVERED once delivered to Production. A bale can be
    delivered once, whole, and only to Production.
    
    The business-visible identity is `shipment_number` + `bale_number`.
    
    Attributes:
        id: Independent technical UUID identity.
        raw_material_batch_id: Reference to the batch that contains this bale.
        bale_number: Business-visible bale number within its batch.
        material: Recorded raw-material classification.
        dtex: Technical linear-density value.
        weight: Gross, container, and net weight measurements.
        status: Current custody lifecycle state.
    """
    
    id: BaleId
    raw_material_batch_id: RawMaterialBatchId
    bale_number: BaleNumber
    material: MaterialType
    dtex: Dtex
    weight: BaleWeight
    status: BaleStatus = BaleStatus.IN_WAREHOUSE

    def __init__(
        self,
        *,
        id: BaleId,
        bale_number: BaleNumber,
        material: MaterialType,
        dtex: Dtex,
        weight: BaleWeight,
        raw_material_batch_id: RawMaterialBatchId,
        status: BaleStatus = BaleStatus.IN_WAREHOUSE,
    ) -> None:
        self.id = id
        self.raw_material_batch_id = raw_material_batch_id
        self.bale_number = bale_number
        self.material = material
        self.dtex = dtex
        self.weight = weight
        self.status = status

    def deliver(self) -> None:
        """Transition this bale to DELIVERED.
        
        The bale must be in IN_WAREHOUSE status. A bale can be delivered once,
        whole, and only to Production. Repeated delivery is rejected.
        
        Raises:
            InvalidBaleStateTransitionError: If the bale is not currently
                IN_WAREHOUSE.
        """
        if self.status is not BaleStatus.IN_WAREHOUSE:
            raise InvalidBaleStateTransitionError(
                f"Bale {self.bale_number.value} is not available in warehouse."
            )
        self.status = BaleStatus.DELIVERED

    @property
    def is_available(self) -> bool:
        """Whether this bale is still under Warehouse custody (IN_WAREHOUSE)."""
        return self.status is BaleStatus.IN_WAREHOUSE
