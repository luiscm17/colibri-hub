from decimal import Decimal

from warehouse.bales.application import ReceivedBaleCommand, RegisterRawMaterialBatchCommand

from backend.tests.support.values import (
    CONTAINER_WEIGHT_KG,
    DTEX,
    GROSS_WEIGHT_KG,
    RECEIVED_AT,
)


def received_bale(number: str = "bale-01") -> ReceivedBaleCommand:
    return ReceivedBaleCommand(
        bale_number=number,
        material_type="cotton",
        dtex=DTEX,
        gross_weight_kg=GROSS_WEIGHT_KG,
        container_weight_kg=CONTAINER_WEIGHT_KG,
    )


def registration_command(
    *, bales: tuple[ReceivedBaleCommand, ...] = (received_bale(),),
    shipment_number: str = "ship-01",
) -> RegisterRawMaterialBatchCommand:
    return RegisterRawMaterialBatchCommand(
        received_at=RECEIVED_AT,
        shipment_number=shipment_number,
        provider_name="  Fiber Supplier  ",
        bales=bales,
    )
