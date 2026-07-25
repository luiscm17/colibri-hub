from typing import Literal

from warehouse.bales.adapters.http.bale_reception_request import BaleReceptionRequest
from warehouse.bales.adapters.http.bale_reception_response import (
    BaleReceptionResponse,
    RegisteredBaleResponse,
)
from warehouse.bales.application.register_raw_material_batch_command import (
    ReceivedBaleCommand,
    RegisterRawMaterialBatchCommand,
)
from warehouse.bales.application.register_raw_material_batch_result import (
    RegisterRawMaterialBatchResult,
)


def _bale_status(status: str) -> Literal["in_warehouse"]:
    if status != "in_warehouse":
        raise ValueError(f"Unexpected registered bale status: {status!r}.")
    return status


def bale_reception_to_input(
    request: BaleReceptionRequest,
) -> RegisterRawMaterialBatchCommand:
    return RegisterRawMaterialBatchCommand(
        received_at=request.received_at,
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
    return BaleReceptionResponse(
        raw_material_batch_id=result.raw_material_batch_id,
        shipment_number=result.shipment_number,
        received_at=result.received_at,
        provider_name=result.provider_name,
        bale_count=result.bale_count,
        bales=tuple(
            RegisteredBaleResponse(
                id=bale.id,
                bale_number=bale.bale_number,
                material_type=bale.material_type,
                dtex=bale.dtex,
                gross_weight_kg=bale.gross_weight_kg,
                container_weight_kg=bale.container_weight_kg,
                status=_bale_status(bale.status),
            )
            for bale in result.bales
        ),
    )
