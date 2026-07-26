from enum import StrEnum


class BaleStatus(StrEnum):
    """Custody lifecycle state for a raw-material bale.
    
    Tracks whether a bale is still under Warehouse custody or has been
    delivered to Production.
    """
    IN_WAREHOUSE = "in_warehouse"
    DELIVERED = "delivered"
