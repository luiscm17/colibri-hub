from dataclasses import dataclass
from datetime import date, datetime

from warehouse.bales.domain.domain_errors import InvalidReceptionDateError


@dataclass(frozen=True, slots=True)
class ReceptionDate:
    """Calendar date recording when a raw material batch was physically received.

    Captures the business date of the reception event without time component.
    Rejects datetime instances to prevent accidental time injection.

    Attributes:
        value: A plain date (no time, no timezone).

    Raises:
        InvalidReceptionDateError: If value is a datetime instance or not a date.
    """

    value: date

    def __post_init__(self) -> None:
        if isinstance(self.value, datetime):
            raise InvalidReceptionDateError("Must be a date, not datetime.")
        if not isinstance(self.value, date):
            raise InvalidReceptionDateError("Must be a date instance.")
