class RawMaterialBatchApplicationError(Exception):
    """Base error for raw-material batch orchestration."""


class DuplicateBaleNumberError(RawMaterialBatchApplicationError):
    """A batch contains duplicate canonical Bale numbers."""


class DuplicateShipmentNumberError(RawMaterialBatchApplicationError):
    """A raw-material batch already uses the shipment number."""


class BaleNotFoundError(RawMaterialBatchApplicationError):
    """The requested bale does not exist for the given business identity."""


class InvalidDateRangeError(RawMaterialBatchApplicationError):
    """The received_from date is later than received_to."""


class InvalidStatusFilterError(RawMaterialBatchApplicationError):
    """The status filter value is not a recognized bale status."""


class DuplicateDeliveryIdentityError(RawMaterialBatchApplicationError):
    """A delivery request contains duplicate bale identities after normalization."""
