from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from warehouse.bales.ports.bale_detail_query import (
    BaleDetailQuery,
    BaleDetailQueryPort,
    BaleDetailResult,
)

_BALE_DETAIL_SQL = text("""\
SELECT
    b.id,
    batch.shipment_number,
    b.bale_number,
    batch.received_at,
    batch.provider_name,
    b.material_type,
    b.dtex,
    b.gross_weight_kg,
    b.container_weight_kg,
    (b.gross_weight_kg - b.container_weight_kg) AS net_weight_kg,
    b.status,
    b.delivery_date
FROM raw_material_bales b
JOIN raw_material_batches batch ON b.raw_material_batch_id = batch.id
WHERE batch.shipment_number = UPPER(:shipment_number)
  AND b.bale_number = UPPER(:bale_number)
""")


class BaleDetailQueryAdapter(BaleDetailQueryPort):
    """SQLAlchemy adapter that retrieves a single bale detail via raw SQL projection."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, query: BaleDetailQuery) -> BaleDetailResult | None:
        """Execute the bale detail query, normalizing path parameters to uppercase."""
        shipment_number = query.shipment_number.strip().upper()
        bale_number = query.bale_number.strip().upper()

        row = self._session.execute(
            _BALE_DETAIL_SQL,
            {"shipment_number": shipment_number, "bale_number": bale_number},
        ).mappings().one_or_none()

        if row is None:
            return None

        return BaleDetailResult(
            id=UUID(str(row["id"])),
            shipment_number=row["shipment_number"],
            bale_number=row["bale_number"],
            received_at=row["received_at"],
            provider_name=row["provider_name"],
            material_type=row["material_type"],
            dtex=row["dtex"],
            gross_weight_kg=row["gross_weight_kg"],
            container_weight_kg=row["container_weight_kg"],
            net_weight_kg=row["net_weight_kg"],
            status=row["status"],
            delivery_date=row["delivery_date"],
        )
