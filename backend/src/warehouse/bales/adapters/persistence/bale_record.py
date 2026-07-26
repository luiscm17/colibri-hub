from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    Numeric,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.record_registry import RecordRegistry


class BaleRecord(RecordRegistry):
    """ORM record for the `raw_material_bales` table.
    
    Maps to an individual bale within a raw-material batch. The `bale_number`
    is unique within a batch through 
    `uq_raw_material_bales_raw_material_batch_bale_number`.
    The `status` check constraint permits `in_warehouse` and `delivered`.
    """
    
    __tablename__ = "raw_material_bales"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_raw_material_bales"),
        ForeignKeyConstraint(
            ("raw_material_batch_id",),
            ("raw_material_batches.id",),
            name="fk_raw_material_bales_raw_material_batch_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "raw_material_batch_id",
            "bale_number",
            name="uq_raw_material_bales_raw_material_batch_bale_number",
        ),
        CheckConstraint(
            "status IN ('in_warehouse', 'delivered')",
            name="ck_raw_material_bales_status",
        ),
        Index(
            "ix_raw_material_bales_raw_material_batch_id",
            "raw_material_batch_id",
        ),
    )
    id: Mapped[UUID] = mapped_column()
    raw_material_batch_id: Mapped[UUID] = mapped_column(nullable=False)
    bale_number: Mapped[str] = mapped_column(String(10), nullable=False)
    material_type: Mapped[str] = mapped_column(String(20), nullable=False)
    dtex: Mapped[Decimal] = mapped_column(Numeric(), nullable=False)
    gross_weight_kg: Mapped[Decimal] = mapped_column(Numeric(), nullable=False)
    container_weight_kg: Mapped[Decimal] = mapped_column(Numeric(), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
