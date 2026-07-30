from collections.abc import Sequence

from warehouse.bales.adapters.persistence.raw_material_batch_record import RawMaterialBatchRecord
from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.raw_material_batch import RawMaterialBatch
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId
from warehouse.bales.domain.reception_date import ReceptionDate
from warehouse.bales.domain.shipment_number import ShipmentNumber


class RawMaterialBatchMapper:
    """Converts between RawMaterialBatch domain entities and ORM records."""
    
    @staticmethod
    def to_record(batch: RawMaterialBatch) -> RawMaterialBatchRecord:
        """Map a domain batch to a persistence record."""
        return RawMaterialBatchRecord(id=batch.id.value, received_at=batch.received_at.value, shipment_number=batch.shipment_number.value, provider_name=batch.provider_name)

    @staticmethod
    def to_domain(record: RawMaterialBatchRecord, bale_ids: Sequence[BaleId]) -> RawMaterialBatch:
        """Map a persistence record back to a domain batch."""
        return RawMaterialBatch(id=RawMaterialBatchId(record.id), received_at=ReceptionDate(record.received_at), shipment_number=ShipmentNumber(record.shipment_number), provider_name=record.provider_name, bale_ids=tuple(bale_ids))
