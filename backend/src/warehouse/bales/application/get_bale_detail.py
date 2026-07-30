from warehouse.bales.application.errors import BaleNotFoundError
from warehouse.bales.ports.bale_detail_query import (
    BaleDetailQuery,
    BaleDetailQueryPort,
    BaleDetailResult,
)


class GetBaleDetail:
    """Use case: retrieve the full detail of a single bale by business identity.

    Delegates the lookup to a read-only query port and raises
    BaleNotFoundError when the bale does not exist.
    """

    def __init__(self, bale_detail_query: BaleDetailQueryPort) -> None:
        self._bale_detail_query = bale_detail_query

    def execute(self, query: BaleDetailQuery) -> BaleDetailResult:
        """Look up a bale by its composite business identity.

        Args:
            query: Contains shipment_number and bale_number identifying the bale.

        Returns:
            The full bale detail projection.

        Raises:
            BaleNotFoundError: When no bale matches the provided identity.
        """
        result = self._bale_detail_query.execute(query)
        if result is None:
            raise BaleNotFoundError(
                f"Bale not found: shipment={query.shipment_number}, "
                f"bale={query.bale_number}"
            )
        return result


__all__ = [
    "BaleDetailQuery",
    "BaleDetailResult",
    "GetBaleDetail",
]
