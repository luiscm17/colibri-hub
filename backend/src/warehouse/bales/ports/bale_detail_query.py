from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BaleDetailQuery:
    """Input contract for the bale detail projection."""

    shipment_number: str
    bale_number: str


@dataclass(frozen=True, slots=True)
class BaleDetailResult:
    """Output contract for the bale detail projection."""

    id: UUID
    shipment_number: str
    bale_number: str
    received_at: date
    provider_name: str
    material_type: str
    dtex: Decimal
    gross_weight_kg: Decimal
    container_weight_kg: Decimal
    net_weight_kg: Decimal
    status: str
    delivery_date: date | None


@runtime_checkable
class BaleDetailQueryPort(Protocol):
    """Read-only query contract for individual bale detail projections.

    Implementations join bales and batches, computing net_weight_kg
    as gross_weight_kg minus container_weight_kg via SQL.
    """

    def execute(self, query: BaleDetailQuery) -> BaleDetailResult | None: ...
