from dataclasses import dataclass
from datetime import datetime

from warehouse.bales.domain.domain_errors import InvalidReceptionDateTimeError


@dataclass(frozen=True, slots=True)
class ReceptionDateTime:
    value: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.value, datetime):
            raise InvalidReceptionDateTimeError("Reception date and time must be a datetime value.")
        if self.value.tzinfo is None or self.value.utcoffset() is None:
            raise InvalidReceptionDateTimeError("Reception date and time must include timezone information.")
