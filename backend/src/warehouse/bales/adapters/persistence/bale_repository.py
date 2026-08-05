from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from warehouse.bales.adapters.persistence.bale_mapper import BaleMapper
from warehouse.bales.adapters.persistence.bale_record import BaleRecord
from warehouse.bales.adapters.persistence.raw_material_batch_record import (
    RawMaterialBatchRecord,
)
from warehouse.bales.domain.bale import Bale
from warehouse.bales.ports.bale_repository import BaleRepository as BaleRepositoryPort


class BaleRepositoryAdapter(BaleRepositoryPort):
    """SQLAlchemy adapter for batch-registering multiple bales."""
    
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_all(self, bales: Sequence[Bale]) -> None:
        """Map domain bales to records and add them to the session."""
        self._session.add_all([BaleMapper.to_record(bale) for bale in bales])

    def find_for_delivery(self, shipment_number: str, bale_number: str) -> Bale | None:
        """Join raw_material_bales with raw_material_batches to resolve business identity."""
        stmt = (
            select(BaleRecord)
            .join(
                RawMaterialBatchRecord,
                BaleRecord.raw_material_batch_id == RawMaterialBatchRecord.id,
            )
            .where(
                RawMaterialBatchRecord.shipment_number == shipment_number.upper(),
                BaleRecord.bale_number == bale_number.upper(),
            )
        )
        record = self._session.execute(stmt).scalars().one_or_none()
        return BaleMapper.to_domain(record) if record else None

    def update_delivery(self, bale: Bale) -> bool:
        """Conditional update: sets delivered + delivery_date only if status is still in_warehouse."""
        stmt = (
            update(BaleRecord)
            .where(
                BaleRecord.id == bale.id.value,
                BaleRecord.status == "in_warehouse",
            )
            .values(status="delivered", delivery_date=bale.delivery_date.value)  # type: ignore[union-attr]
        )
        result = self._session.execute(stmt)
        self._session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]
