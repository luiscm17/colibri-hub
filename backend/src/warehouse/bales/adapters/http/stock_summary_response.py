from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class _HttpResponseModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class StockSummaryResponse(_HttpResponseModel):
    """HTTP response model for the aggregate stock summary endpoint.

    Returns bale counts grouped by status and net weight totals computed
    via SQL aggregation in PostgreSQL.

    Attributes:
        total_bale_count: Total number of bales matching the applied filters.
        in_warehouse_bale_count: Bales currently in warehouse.
        delivered_bale_count: Bales already delivered.
        net_weight_total_kg: Sum of net weights across all matched bales.
        net_weight_in_warehouse_kg: Net weight sum for in-warehouse bales.
        net_weight_delivered_kg: Net weight sum for delivered bales.
    """

    total_bale_count: int
    in_warehouse_bale_count: int
    delivered_bale_count: int
    net_weight_total_kg: Decimal
    net_weight_in_warehouse_kg: Decimal
    net_weight_delivered_kg: Decimal
