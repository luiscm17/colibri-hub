from warehouse.bales.application.errors import (
    InvalidDateRangeError,
    InvalidStatusFilterError,
)
from warehouse.bales.ports.stock_summary_query import (
    StockSummaryQuery,
    StockSummaryQueryPort,
    StockSummaryResult,
)

_VALID_STATUSES = {"in_warehouse", "delivered"}


class GetStockSummary:
    """Query use case that validates filters and delegates to the stock summary port."""

    def __init__(self, stock_summary_query: StockSummaryQueryPort) -> None:
        self._stock_summary_query = stock_summary_query

    def execute(self, query: StockSummaryQuery) -> StockSummaryResult:
        if (
            query.received_from is not None
            and query.received_to is not None
            and query.received_from > query.received_to
        ):
            raise InvalidDateRangeError(
                "received_from must not be later than received_to."
            )

        if query.status is not None and query.status not in _VALID_STATUSES:
            raise InvalidStatusFilterError(
                f"Invalid status filter '{query.status}'. "
                f"Must be one of: {', '.join(sorted(_VALID_STATUSES))}."
            )

        return self._stock_summary_query.execute(query)


# Re-export port types for convenience.
__all__ = [
    "GetStockSummary",
    "StockSummaryQuery",
    "StockSummaryResult",
]
