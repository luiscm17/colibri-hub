from dataclasses import dataclass
from datetime import datetime

from warehouse.bales.domain.domain_errors import InvalidReceptionDateTimeError


@dataclass(frozen=True, slots=True)
class ReceptionDateTime:
    """Timestamp recording when a raw material batch was physically received.
    
    Captures the business date and time of the reception event. The timestamp
    must include timezone information for temporal consistency.
    
    Attributes:
        value: Datetime with timezone information.
    
    Raises:
        InvalidReceptionDateTimeError: If value is not a datetime or lacks
            timezone information.
    """
    
    value: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.value, datetime):
            raise InvalidReceptionDateTimeError("Reception date and time must be a datetime value.")
        if self.value.tzinfo is None or self.value.utcoffset() is None:
            raise InvalidReceptionDateTimeError("Reception date and time must include timezone information.")
