from warehouse.bales.application.errors import (
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
)
from warehouse.bales.application.register_raw_material_batch_command import (
    ReceivedBaleCommand,
    RegisterRawMaterialBatchCommand,
)
from warehouse.bales.application.register_raw_material_batch_result import (
    RegisterRawMaterialBatchResult,
    RegisteredBaleResult,
)
from warehouse.bales.domain.bale import Bale
from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.raw_material_batch import RawMaterialBatch
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId
from warehouse.bales.domain.reception_datetime import ReceptionDateTime
from warehouse.bales.domain.shipment_number import ShipmentNumber
from warehouse.bales.ports import (
    BaleRepository,
    DuplicateBaleNumberConflict,
    DuplicateShipmentNumberConflict,
    IdentityGenerator,
    RawMaterialBatchRepository,
    Transaction,
)


class RegisterRawMaterialBatch:
    def __init__(
        self,
        reception_repository: RawMaterialBatchRepository,
        bale_repository: BaleRepository,
        warehouse_transaction: Transaction,
        identity_generator: IdentityGenerator,
    ) -> None:
        self._raw_material_batch_repository = reception_repository
        self._bale_repository = bale_repository
        self._transaction = warehouse_transaction
        self._identity_generator = identity_generator

    def execute(
        self,
        command: RegisterRawMaterialBatchCommand,
    ) -> RegisterRawMaterialBatchResult:
        bale_numbers = self._canonical_bale_numbers(command.bales)
        self._ensure_unique_bale_numbers(bale_numbers)
        batch_id = RawMaterialBatchId(self._identity_generator.next_id())
        bales = self._create_bales(batch_id, command.bales, bale_numbers)
        batch = RawMaterialBatch(
            id=batch_id,
            received_at=ReceptionDateTime(command.received_at),
            shipment_number=ShipmentNumber(command.shipment_number),
            provider_name=command.provider_name,
            bale_ids=tuple(bale.id for bale in bales),
        )
        try:
            with self._transaction:
                self._raw_material_batch_repository.add(batch)
                self._bale_repository.add_all(bales)
                self._transaction.commit()
        except DuplicateBaleNumberConflict as error:
            raise DuplicateBaleNumberError(
                "Raw material reception cannot contain duplicate bale numbers."
            ) from error
        except DuplicateShipmentNumberConflict as error:
            raise DuplicateShipmentNumberError(
                "Shipment number is already registered."
            ) from error
        return RegisterRawMaterialBatchResult(
            reception_id=batch.id.value,
            shipment_number=batch.shipment_number.value,
            received_at=batch.received_at.value,
            provider_name=batch.provider_name,
            bale_count=batch.bale_count,
            bales=tuple(
                RegisteredBaleResult(
                    id=bale.id.value,
                    bale_number=bale.bale_number.value,
                    material_type=bale.material.value,
                    dtex=bale.dtex.value,
                    gross_weight_kg=bale.weight.gross_kg,
                    container_weight_kg=bale.weight.container_kg,
                    status=bale.status.value,
                )
                for bale in bales
            ),
        )

    def _create_bales(
        self,
        batch_id: RawMaterialBatchId,
        commands: tuple[ReceivedBaleCommand, ...],
        bale_numbers: tuple[BaleNumber, ...],
    ) -> tuple[Bale, ...]:
        return tuple(
            Bale(
                id=BaleId(self._identity_generator.next_id()),
                raw_material_batch_id=batch_id,
                bale_number=bale_number,
                material=MaterialType(command.material_type),
                dtex=Dtex(command.dtex),
                weight=BaleWeight(
                    gross_kg=command.gross_weight_kg,
                    container_kg=command.container_weight_kg,
                ),
            )
            for command, bale_number in zip(commands, bale_numbers, strict=True)
        )

    @staticmethod
    def _canonical_bale_numbers(
        commands: tuple[ReceivedBaleCommand, ...],
    ) -> tuple[BaleNumber, ...]:
        return tuple(BaleNumber(command.bale_number) for command in commands)

    @staticmethod
    def _ensure_unique_bale_numbers(bale_numbers: tuple[BaleNumber, ...]) -> None:
        if len(bale_numbers) != len(set(bale_numbers)):
            raise DuplicateBaleNumberError(
                "Raw material reception cannot contain duplicate bale numbers."
            )
