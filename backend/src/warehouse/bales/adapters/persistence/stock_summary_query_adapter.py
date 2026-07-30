from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from warehouse.bales.ports.stock_summary_query import (
    StockSummaryQuery,
    StockSummaryQueryPort,
    StockSummaryResult,
)


class StockSummaryQueryAdapter(StockSummaryQueryPort):
    """Computes aggregate stock counts and net weights via a single SQL query.

    Filters are applied dynamically based on non-None query parameters.
    Uses PostgreSQL FILTER clauses for conditional aggregation.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, query: StockSummaryQuery) -> StockSummaryResult:
        conditions: list[str] = []
        params: dict[str, object] = {}

        if query.received_from is not None:
            conditions.append("batch.received_at >= :received_from")
            params["received_from"] = query.received_from

        if query.received_to is not None:
            conditions.append("batch.received_at <= :received_to")
            params["received_to"] = query.received_to

        if query.shipment_number is not None:
            conditions.append("batch.shipment_number = UPPER(:shipment_number)")
            params["shipment_number"] = query.shipment_number

        if query.status is not None:
            conditions.append("b.status = :status")
            params["status"] = query.status

        if query.provider_name is not None:
            conditions.append(
                "LOWER(TRIM(batch.provider_name)) = LOWER(TRIM(:provider_name))"
            )
            params["provider_name"] = query.provider_name

        if query.material_type is not None:
            conditions.append("b.material_type = UPPER(:material_type)")
            params["material_type"] = query.material_type

        if query.dtex is not None:
            conditions.append("b.dtex = :dtex")
            params["dtex"] = query.dtex

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        sql = text(f"""
            SELECT
                COUNT(*) AS total_bale_count,
                COUNT(*) FILTER (WHERE b.status = 'in_warehouse') AS in_warehouse_bale_count,
                COUNT(*) FILTER (WHERE b.status = 'delivered') AS delivered_bale_count,
                COALESCE(SUM(b.gross_weight_kg - b.container_weight_kg), 0) AS net_weight_total_kg,
                COALESCE(SUM(b.gross_weight_kg - b.container_weight_kg) FILTER (WHERE b.status = 'in_warehouse'), 0) AS net_weight_in_warehouse_kg,
                COALESCE(SUM(b.gross_weight_kg - b.container_weight_kg) FILTER (WHERE b.status = 'delivered'), 0) AS net_weight_delivered_kg
            FROM raw_material_bales b
            JOIN raw_material_batches batch ON b.raw_material_batch_id = batch.id
            WHERE {where_clause}
        """)

        row = self._session.execute(sql, params).one()

        return StockSummaryResult(
            total_bale_count=row.total_bale_count,
            in_warehouse_bale_count=row.in_warehouse_bale_count,
            delivered_bale_count=row.delivered_bale_count,
            net_weight_total_kg=Decimal(str(row.net_weight_total_kg)),
            net_weight_in_warehouse_kg=Decimal(str(row.net_weight_in_warehouse_kg)),
            net_weight_delivered_kg=Decimal(str(row.net_weight_delivered_kg)),
        )
