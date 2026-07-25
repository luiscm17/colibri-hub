from sqlalchemy.orm import Session

from warehouse.bales.adapters.persistence.raw_material_batch_mapper import RawMaterialBatchMapper
from warehouse.bales.domain.raw_material_batch import RawMaterialBatch
from warehouse.bales.ports.raw_material_batch_repository import RawMaterialBatchRepository as RawMaterialBatchRepositoryPort


class RawMaterialBatchRepositoryAdapter(RawMaterialBatchRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, batch: RawMaterialBatch) -> None:
        self._session.add(RawMaterialBatchMapper.to_record(batch))
        self._session.flush()
