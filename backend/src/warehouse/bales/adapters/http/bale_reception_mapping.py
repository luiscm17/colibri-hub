from datetime import date

from warehouse.bales.adapters.http.bale_reception_request import BaleReceptionRequest
from warehouse.bales.adapters.http.bale_reception_response import (
    BaleReceptionResponse,
)
from warehouse.bales.application.register_raw_material_batch_command import (
    ReceivedBaleCommand,
    RegisterRawMaterialBatchCommand,
)
from warehouse.bales.application.register_raw_material_batch_result import (
    RegisterRawMaterialBatchResult,
)


def bale_reception_to_input(
    request: BaleReceptionRequest,
) -> RegisterRawMaterialBatchCommand:
    """Map an HTTP request to the application command.

    Args:
        request: The validated HTTP request model.

    Returns:
        Application command ready for use case execution.
    """
    return RegisterRawMaterialBatchCommand(
        received_at=date.fromisoformat(request.received_at),
        shipment_number=request.shipment_number,
        provider_name=request.provider_name,
        bales=tuple(
            ReceivedBaleCommand(
                bale_number=bale.bale_number,
                material_type=bale.material_type,
                dtex=bale.dtex,
                gross_weight_kg=bale.gross_weight_kg,
                container_weight_kg=bale.container_weight_kg,
            )
            for bale in request.bales
        ),
    )


def bale_reception_to_response(
    result: RegisterRawMaterialBatchResult,
) -> BaleReceptionResponse:
    """Map an application result to the HTTP response model.

    Args:
        result: The use case execution result.

    Returns:
        HTTP response model for the API client.
    """
    return BaleReceptionResponse(
        raw_material_batch_id=result.raw_material_batch_id,
        shipment_number=result.shipment_number,
        received_at=result.received_at,
        provider_name=result.provider_name,
        bale_count=result.bale_count,
    )
