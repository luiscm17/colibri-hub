class DuplicateBaleNumberConflict(Exception):
    """A batch contains duplicate canonical Bale numbers."""


class DuplicateShipmentNumberConflict(Exception):
    """A transaction persisted an existing shipment number."""
