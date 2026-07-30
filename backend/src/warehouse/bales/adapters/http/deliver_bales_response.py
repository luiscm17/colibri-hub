from pydantic import BaseModel, ConfigDict


class _HttpResponseModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DeliveryErrorResponse(_HttpResponseModel):
    """Per-bale error detail within a delivery outcome.

    Attributes:
        code: Machine-readable error code (e.g. 'not_found', 'already_delivered').
        message: Human-readable error description.
    """

    code: str
    message: str


class DeliveryOutcomeResponse(_HttpResponseModel):
    """Per-bale result within a batch delivery response.

    Attributes:
        shipment_number: Shipment the bale belongs to.
        bale_number: Business-visible bale number.
        status: Outcome of the delivery attempt ('delivered', 'already_delivered',
            'not_found', or 'error').
        error: Error detail when the delivery attempt failed; None on success.
    """

    shipment_number: str
    bale_number: str
    status: str
    error: DeliveryErrorResponse | None = None


class DeliverBalesResponse(_HttpResponseModel):
    """HTTP response model for a batch delivery operation.

    Attributes:
        delivery_date: Business date applied to all delivered bales.
        delivered_count: Number of bales successfully transitioned.
        failed_count: Number of bales that could not be delivered.
        results: Per-bale outcome in submission order.
    """

    delivery_date: str
    delivered_count: int
    failed_count: int
    results: tuple[DeliveryOutcomeResponse, ...]
