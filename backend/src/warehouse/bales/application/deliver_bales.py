from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from warehouse.bales.application.errors import DuplicateDeliveryIdentityError
from warehouse.bales.domain.bale_status import BaleStatus
from warehouse.bales.domain.delivery_date import DeliveryDate
from warehouse.bales.ports.bale_repository import BaleRepository
from warehouse.bales.ports.transaction import Transaction


@dataclass(frozen=True, slots=True)
class BaleIdentityCommand:
    """Identity of a single bale within a delivery request."""

    shipment_number: str
    bale_number: str


@dataclass(frozen=True, slots=True)
class DeliverBalesCommand:
    """Command to deliver one or more bales on a given date."""

    delivery_date: date
    bales: tuple[BaleIdentityCommand, ...]


@dataclass(frozen=True, slots=True)
class BaleDeliveryOutcome:
    """Per-bale result of a delivery attempt."""

    shipment_number: str
    bale_number: str
    status: str  # "delivered" | "already_delivered" | "not_found" | "error"
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class DeliverBalesResult:
    """Aggregate result of a batch delivery operation."""

    delivery_date: date
    delivered_count: int
    failed_count: int
    results: tuple[BaleDeliveryOutcome, ...]


class DeliverBales:
    """Use case: deliver one or more bales with best-effort per-bale processing.

    Each bale is processed independently. A failure for one bale does NOT
    roll back others. The transaction port is used for the overall session
    but each bale flush is independent.

    Algorithm:
        1. Validate no duplicate identities after normalization (uppercase).
        2. Create DeliveryDate value object (validates the date).
        3. For each bale identity in order:
           a. Look up bale by business identity.
           b. If not found -> not_found outcome.
           c. If already delivered -> already_delivered outcome.
           d. Deliver and persist -> delivered outcome.
           e. On unexpected error -> error outcome.
        4. Return result with counts.
    """

    def __init__(
        self,
        bale_repository: BaleRepository,
        transaction: Transaction,
    ) -> None:
        self._bale_repository = bale_repository
        self._transaction = transaction

    def execute(self, command: DeliverBalesCommand) -> DeliverBalesResult:
        """Process the delivery command and return per-bale results."""
        self._validate_no_duplicates(command.bales)
        delivery_date = DeliveryDate(command.delivery_date)

        outcomes: list[BaleDeliveryOutcome] = []

        with self._transaction:
            for identity in command.bales:
                outcome = self._process_bale(identity, delivery_date)
                outcomes.append(outcome)
            self._transaction.commit()

        delivered_count = sum(
            1 for o in outcomes if o.status == "delivered"
        )
        failed_count = len(outcomes) - delivered_count

        return DeliverBalesResult(
            delivery_date=command.delivery_date,
            delivered_count=delivered_count,
            failed_count=failed_count,
            results=tuple(outcomes),
        )

    def _process_bale(
        self,
        identity: BaleIdentityCommand,
        delivery_date: DeliveryDate,
    ) -> BaleDeliveryOutcome:
        """Process a single bale delivery attempt independently."""
        shipment = identity.shipment_number.upper()
        bale_num = identity.bale_number.upper()

        try:
            bale = self._bale_repository.find_for_delivery(shipment, bale_num)

            if bale is None:
                return BaleDeliveryOutcome(
                    shipment_number=shipment,
                    bale_number=bale_num,
                    status="not_found",
                    error_code="bale_not_found",
                    error_message=f"Bale {shipment}/{bale_num} not found.",
                )

            if bale.status is BaleStatus.DELIVERED:
                return BaleDeliveryOutcome(
                    shipment_number=shipment,
                    bale_number=bale_num,
                    status="already_delivered",
                    error_code="already_delivered",
                    error_message=f"Bale {shipment}/{bale_num} is already delivered.",
                )

            bale.deliver(delivery_date)
            self._bale_repository.update_delivery(bale)

            return BaleDeliveryOutcome(
                shipment_number=shipment,
                bale_number=bale_num,
                status="delivered",
            )

        except Exception as exc:
            return BaleDeliveryOutcome(
                shipment_number=shipment,
                bale_number=bale_num,
                status="error",
                error_code="unexpected_error",
                error_message=str(exc),
            )

    @staticmethod
    def _validate_no_duplicates(
        bales: tuple[BaleIdentityCommand, ...],
    ) -> None:
        """Reject the request if any bale identities are duplicated after normalization."""
        seen: set[tuple[str, str]] = set()
        for identity in bales:
            normalized = (
                identity.shipment_number.upper(),
                identity.bale_number.upper(),
            )
            if normalized in seen:
                raise DuplicateDeliveryIdentityError(
                    f"Duplicate bale identity after normalization: "
                    f"{normalized[0]}/{normalized[1]}."
                )
            seen.add(normalized)
