from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.record_registry import RecordRegistry


class BaleRecord(RecordRegistry):
    __tablename__ = "raw_material_bales"
    __table_args__ = (UniqueConstraint("reception_id", "bale_number", name="uq_raw_material_bales_reception_bale_number"),)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    reception_id: Mapped[UUID] = mapped_column(ForeignKey("raw_material_receptions.id", ondelete="RESTRICT"), nullable=False, index=True)
    bale_number: Mapped[str] = mapped_column(String(10), nullable=False)
    material_type: Mapped[str] = mapped_column(String(20), nullable=False)
    dtex: Mapped[Decimal] = mapped_column(Numeric(), nullable=False)
    gross_weight_kg: Mapped[Decimal] = mapped_column(Numeric(), nullable=False)
    container_weight_kg: Mapped[Decimal] = mapped_column(Numeric(), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
