class RawMaterialBatchApplicationError(Exception):
    """Base error for raw-material batch orchestration."""


class DuplicateBaleNumberError(RawMaterialBatchApplicationError):
    """A batch contains duplicate canonical Bale numbers."""


class DuplicateShipmentNumberError(RawMaterialBatchApplicationError):
    """A raw-material batch already uses the shipment number."""
