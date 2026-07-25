from collections.abc import Sequence

from warehouse.bales.adapters.persistence.raw_material_batch_record import RawMaterialBatchRecord
from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.raw_material_batch import RawMaterialBatch
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId
from warehouse.bales.domain.reception_datetime import ReceptionDateTime
from warehouse.bales.domain.shipment_number import ShipmentNumber


class RawMaterialBatchMapper:
    @staticmethod
    def to_record(batch: RawMaterialBatch) -> RawMaterialBatchRecord:
        return RawMaterialBatchRecord(id=batch.id.value, received_at=batch.received_at.value, shipment_number=batch.shipment_number.value, provider_name=batch.provider_name)

    @staticmethod
    def to_domain(record: RawMaterialBatchRecord, bale_ids: Sequence[BaleId]) -> RawMaterialBatch:
        return RawMaterialBatch(id=RawMaterialBatchId(record.id), received_at=ReceptionDateTime(record.received_at), shipment_number=ShipmentNumber(record.shipment_number), provider_name=record.provider_name, bale_ids=tuple(bale_ids))
