from dataclasses import dataclass
from datetime import date, datetime

from warehouse.bales.domain.domain_errors import InvalidDeliveryDateError


@dataclass(frozen=True, slots=True)
class DeliveryDate:
    """Calendar date recording when a bale was physically delivered.

    Accepts only plain `datetime.date` instances. Rejects `datetime.datetime`
    (including timezone-aware) to prevent accidental time injection.

    Attributes:
        value: A plain calendar date (no time component).

    Raises:
        InvalidDeliveryDateError: If value is a datetime instance or not a date.
    """

    value: date

    def __post_init__(self) -> None:
        if isinstance(self.value, datetime):
            raise InvalidDeliveryDateError("Must be a date, not datetime.")
        if not isinstance(self.value, date):
            raise InvalidDeliveryDateError("Must be a date instance.")
