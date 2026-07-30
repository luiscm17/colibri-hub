from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import re
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse

from warehouse.bales.adapters.http.bale_detail_response import BaleDetailResponse
from warehouse.bales.adapters.http.bale_reception_mapping import (
    bale_reception_to_input,
    bale_reception_to_response,
)
from warehouse.bales.adapters.http.bale_reception_request import BaleReceptionRequest
from warehouse.bales.adapters.http.bale_reception_response import BaleReceptionResponse
from warehouse.bales.adapters.http.deliver_bales_request import DeliverBalesRequest
from warehouse.bales.adapters.http.deliver_bales_response import (
    DeliverBalesResponse,
    DeliveryErrorResponse,
    DeliveryOutcomeResponse,
)
from warehouse.bales.adapters.http.error_mapping import error_json_response
from warehouse.bales.adapters.http.error_response import (
    ErrorResponse,
    FieldErrorResponse,
)
from warehouse.bales.adapters.http.stock_summary_response import StockSummaryResponse
from warehouse.bales.application.deliver_bales import (
    BaleIdentityCommand,
    DeliverBales,
    DeliverBalesCommand,
    DeliverBalesResult,
)
from warehouse.bales.application.get_bale_detail import (
    BaleDetailQuery,
    BaleDetailResult,
    GetBaleDetail,
)
from warehouse.bales.application.get_stock_summary import (
    GetStockSummary,
    StockSummaryQuery,
    StockSummaryResult,
)
from warehouse.bales.application.register_raw_material_batch import (
    RegisterRawMaterialBatch,
)


@dataclass(frozen=True)
class BaleUseCases:
    """Typed dependency container holding all bale-related use cases.

    Replaces the single-use-case provider pattern with a multi-use-case
    container that the router resolves via FastAPI's dependency injection.
    """

    register: RegisterRawMaterialBatch
    stock_summary: GetStockSummary
    bale_detail: GetBaleDetail
    deliver: DeliverBales


UseCaseProvider = Callable[..., BaleUseCases]


def create_router(use_case_provider: UseCaseProvider) -> APIRouter:
    """Create the HTTP router for bale management endpoints.

    Defines four endpoints:
    - POST /bales — register a raw-material batch
    - GET /bales — aggregate stock summary
    - GET /bales/{shipment_number}/{bale_number} — individual bale detail
    - POST /bales/deliver — batch delivery

    Args:
        use_case_provider: FastAPI dependency that resolves the BaleUseCases container.

    Returns:
        Configured APIRouter with all bale endpoints.
    """
    router = APIRouter(prefix="/bales")

    @router.post(
        "",
        response_model=BaleReceptionResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            status.HTTP_409_CONFLICT: {
                "model": ErrorResponse,
                "description": "The shipment number is already registered.",
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "model": ErrorResponse,
                "description": "The request or reception violates a validation rule.",
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "model": ErrorResponse,
                "description": "Unexpected internal server error.",
            },
        },
    )
    def register(
        request: BaleReceptionRequest,
        use_cases: Annotated[BaleUseCases, Depends(use_case_provider)],
    ) -> BaleReceptionResponse:
        """POST /bales — register a complete raw-material batch.

        Accepts the batch header and all its bales in one request.
        Returns 201 on success, 409 on duplicate shipment number,
        422 on validation errors, and 500 on unexpected errors.
        """
        return bale_reception_to_response(
            use_cases.register.execute(bale_reception_to_input(request))
        )

    @router.get(
        "",
        response_model=StockSummaryResponse,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "model": ErrorResponse,
                "description": "Invalid filter parameters.",
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "model": ErrorResponse,
                "description": "Unexpected internal server error.",
            },
        },
    )
    def stock_summary(
        use_cases: Annotated[BaleUseCases, Depends(use_case_provider)],
        received_from: Annotated[str | None, Query()] = None,
        received_to: Annotated[str | None, Query()] = None,
        shipment_number: Annotated[str | None, Query()] = None,
        status_filter: Annotated[str | None, Query(alias="status")] = None,
        provider_name: Annotated[str | None, Query()] = None,
        material_type: Annotated[str | None, Query()] = None,
        dtex: Annotated[str | None, Query()] = None,
    ) -> StockSummaryResponse | JSONResponse:
        """GET /bales — aggregate stock summary with optional filters.

        All query parameters are optional. Filters are applied conjunctively.
        Returns 200 with counts and weights (zero when no matches).
        """
        query_or_error = _build_stock_summary_query(
            received_from=received_from,
            received_to=received_to,
            shipment_number=shipment_number,
            status_filter=status_filter,
            provider_name=provider_name,
            material_type=material_type,
            dtex=dtex,
        )
        if isinstance(query_or_error, JSONResponse):
            return query_or_error

        result = use_cases.stock_summary.execute(query_or_error)
        return _map_stock_summary_response(result)

    @router.get(
        "/{shipment_number}/{bale_number}",
        response_model=BaleDetailResponse,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorResponse,
                "description": "The bale was not found.",
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "model": ErrorResponse,
                "description": "Path parameter validation failed.",
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "model": ErrorResponse,
                "description": "Unexpected internal server error.",
            },
        },
    )
    def bale_detail(
        shipment_number: str,
        bale_number: str,
        use_cases: Annotated[BaleUseCases, Depends(use_case_provider)],
    ) -> BaleDetailResponse | JSONResponse:
        """GET /bales/{shipment_number}/{bale_number} — individual bale detail.

        Path parameters are validated: non-empty after strip, ≤10 chars.
        Returns 200 with full bale attributes, 404 if not found.
        """
        validation_error = _validate_path_param(shipment_number, "shipment_number")
        if validation_error is not None:
            return validation_error
        validation_error = _validate_path_param(bale_number, "bale_number")
        if validation_error is not None:
            return validation_error

        result = use_cases.bale_detail.execute(
            BaleDetailQuery(
                shipment_number=shipment_number.strip(),
                bale_number=bale_number.strip(),
            )
        )
        return _map_bale_detail_response(result)

    @router.post(
        "/deliver",
        response_model=DeliverBalesResponse,
        responses={
            status.HTTP_200_OK: {
                "description": "All bales delivered successfully.",
            },
            status.HTTP_207_MULTI_STATUS: {
                "model": DeliverBalesResponse,
                "description": "Mixed results — some bales failed.",
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "model": ErrorResponse,
                "description": "Request validation failed.",
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "model": ErrorResponse,
                "description": "Unexpected internal server error.",
            },
        },
    )
    def deliver_bales(
        request: DeliverBalesRequest,
        response: Response,
        use_cases: Annotated[BaleUseCases, Depends(use_case_provider)],
    ) -> DeliverBalesResponse:
        """POST /bales/deliver — batch delivery with per-bale results.

        Returns 200 when all bales are delivered, 207 when results are mixed.
        """
        command = _build_deliver_command(request)
        result = use_cases.deliver.execute(command)

        if result.failed_count > 0:
            response.status_code = status.HTTP_207_MULTI_STATUS

        return _map_deliver_response(result)

    return router


# ---------------------------------------------------------------------------
# Private mapping and validation helpers
# ---------------------------------------------------------------------------


def _validate_path_param(value: str, field_name: str) -> JSONResponse | None:
    """Validate a path parameter: non-empty after strip, ≤10 chars.

    Returns a 422 JSONResponse if validation fails, None if valid.
    """
    stripped = value.strip()
    if not stripped:
        return error_json_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="request_validation_error",
            message=f"{field_name} must not be empty.",
            fields=(
                FieldErrorResponse(
                    path=field_name,
                    message=f"{field_name} must not be empty.",
                ),
            ),
        )
    if len(stripped) > 10:
        return error_json_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="request_validation_error",
            message=f"{field_name} must not exceed 10 characters.",
            fields=(
                FieldErrorResponse(
                    path=field_name,
                    message=f"{field_name} must not exceed 10 characters.",
                ),
            ),
        )
    return None


def _build_stock_summary_query(
    *,
    received_from: str | None,
    received_to: str | None,
    shipment_number: str | None,
    status_filter: str | None,
    provider_name: str | None,
    material_type: str | None,
    dtex: str | None,
) -> StockSummaryQuery | JSONResponse:
    """Parse and build a StockSummaryQuery from raw query parameter strings.

    Returns either the parsed query or a 422 JSONResponse on validation failure.
    """
    parsed_from: date | None = None
    parsed_to: date | None = None
    parsed_dtex: Decimal | None = None

    if received_from:
        result = _parse_date_param(received_from, "received_from")
        if isinstance(result, JSONResponse):
            return result
        parsed_from = result

    if received_to:
        result = _parse_date_param(received_to, "received_to")
        if isinstance(result, JSONResponse):
            return result
        parsed_to = result

    if dtex:
        dtex_result = _parse_decimal_param(dtex, "dtex")
        if isinstance(dtex_result, JSONResponse):
            return dtex_result
        parsed_dtex = dtex_result

    return StockSummaryQuery(
        received_from=parsed_from,
        received_to=parsed_to,
        shipment_number=shipment_number,
        status=status_filter,
        provider_name=provider_name,
        material_type=material_type,
        dtex=parsed_dtex,
    )


def _parse_date_param(value: str, field_name: str) -> date | JSONResponse:
    """Parse a date query parameter. Returns date or 422 JSONResponse on failure."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return error_json_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="request_validation_error",
            message=f"{field_name} must be a valid ISO date in YYYY-MM-DD format.",
            fields=(
                FieldErrorResponse(
                    path=field_name,
                    message=f"{field_name} must be a valid ISO date in YYYY-MM-DD format.",
                ),
            ),
        )
    try:
        return date.fromisoformat(value)
    except ValueError:
        return error_json_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="request_validation_error",
            message=f"{field_name} must be a valid calendar date.",
            fields=(
                FieldErrorResponse(
                    path=field_name,
                    message=f"{field_name} must be a valid calendar date.",
                ),
            ),
        )


def _parse_decimal_param(value: str, field_name: str) -> Decimal | JSONResponse:
    """Parse a decimal query parameter. Returns Decimal or 422 JSONResponse on failure."""
    try:
        result = Decimal(value)
    except InvalidOperation:
        return error_json_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="request_validation_error",
            message=f"{field_name} must be a valid decimal value.",
            fields=(
                FieldErrorResponse(
                    path=field_name,
                    message=f"{field_name} must be a valid decimal value.",
                ),
            ),
        )
    if not result.is_finite():
        return error_json_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="request_validation_error",
            message=f"{field_name} must be a finite decimal value.",
            fields=(
                FieldErrorResponse(
                    path=field_name,
                    message=f"{field_name} must be a finite decimal value.",
                ),
            ),
        )
    return result


def _map_stock_summary_response(result: StockSummaryResult) -> StockSummaryResponse:
    """Map application result to HTTP response model."""
    return StockSummaryResponse(
        total_bale_count=result.total_bale_count,
        in_warehouse_bale_count=result.in_warehouse_bale_count,
        delivered_bale_count=result.delivered_bale_count,
        net_weight_total_kg=result.net_weight_total_kg,
        net_weight_in_warehouse_kg=result.net_weight_in_warehouse_kg,
        net_weight_delivered_kg=result.net_weight_delivered_kg,
    )


def _map_bale_detail_response(result: BaleDetailResult) -> BaleDetailResponse:
    """Map application result to HTTP response model."""
    return BaleDetailResponse(
        id=result.id,
        shipment_number=result.shipment_number,
        bale_number=result.bale_number,
        received_at=result.received_at.isoformat(),
        provider_name=result.provider_name,
        material_type=result.material_type,
        dtex=result.dtex,
        gross_weight_kg=result.gross_weight_kg,
        container_weight_kg=result.container_weight_kg,
        net_weight_kg=result.net_weight_kg,
        status=result.status,
        delivery_date=result.delivery_date.isoformat() if result.delivery_date else None,
    )


def _build_deliver_command(request: DeliverBalesRequest) -> DeliverBalesCommand:
    """Map HTTP request model to application command."""
    return DeliverBalesCommand(
        delivery_date=date.fromisoformat(request.delivery_date),
        bales=tuple(
            BaleIdentityCommand(
                shipment_number=bale.shipment_number,
                bale_number=bale.bale_number,
            )
            for bale in request.bales
        ),
    )


def _map_deliver_response(result: DeliverBalesResult) -> DeliverBalesResponse:
    """Map application result to HTTP response model."""
    return DeliverBalesResponse(
        delivery_date=result.delivery_date.isoformat(),
        delivered_count=result.delivered_count,
        failed_count=result.failed_count,
        results=tuple(
            DeliveryOutcomeResponse(
                shipment_number=outcome.shipment_number,
                bale_number=outcome.bale_number,
                status=outcome.status,
                error=DeliveryErrorResponse(
                    code=outcome.error_code,
                    message=outcome.error_message,
                )
                if outcome.error_code
                else None,
            )
            for outcome in result.results
        ),
    )
