from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, PrimaryKeyConstraint, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.record_registry import RecordRegistry


class RawMaterialBatchRecord(RecordRegistry):
    __tablename__ = "raw_material_batches"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_raw_material_batches"),
        UniqueConstraint("shipment_number", name="uq_raw_material_batches_shipment_number"),
    )
    id: Mapped[UUID] = mapped_column()
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    shipment_number: Mapped[str] = mapped_column(String(10), nullable=False)
    provider_name: Mapped[str] = mapped_column(Text(), nullable=False)
