from copy import deepcopy


VALID_BALE_RECEPTION_PAYLOAD = {
    "shipment_number": "ship-01",
    "received_at": "2026-07-25T10:30:00Z",
    "provider_name": "Fiber Supplier",
    "bales": [
        {
            "bale_number": "bale-01",
            "material_type": "cotton",
            "dtex": "200.5",
            "gross_weight_kg": "25.5",
            "container_weight_kg": "0.5",
        }
    ],
}


def bale_reception_payload() -> dict[str, object]:
    return deepcopy(VALID_BALE_RECEPTION_PAYLOAD)
