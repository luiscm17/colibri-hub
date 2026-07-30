from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class StockSummaryQuery:
    """Input contract for the stock summary projection."""

    received_from: date | None = None
    received_to: date | None = None
    shipment_number: str | None = None
    status: str | None = None
    provider_name: str | None = None
    material_type: str | None = None
    dtex: Decimal | None = None


@dataclass(frozen=True, slots=True)
class StockSummaryResult:
    """Output contract for the stock summary projection."""

    total_bale_count: int
    in_warehouse_bale_count: int
    delivered_bale_count: int
    net_weight_total_kg: Decimal
    net_weight_in_warehouse_kg: Decimal
    net_weight_delivered_kg: Decimal


@runtime_checkable
class StockSummaryQueryPort(Protocol):
    """Read-only query contract for aggregate stock summary projections.

    Implementations compute counts and net weights via SQL aggregation
    without loading individual bales into application memory.
    """

    def execute(self, query: StockSummaryQuery) -> StockSummaryResult: ...
