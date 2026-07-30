import type { DeliveryInput, DeliveryOutcome, DeliveryResponse } from '../model/delivery'
import { normalizeIdentifier } from '../model/validation'
import type { RegisterBatchInput, RegisteredBatch } from '../model/reception'
import type { BaleDetail, StockFilters, StockSummary } from '../model/stock'
import type { BaleDetailDto, DeliverBalesDto, DeliveryOutcomeDto, DeliveryResponseDto, RegisterBatchDto, RegisteredBatchDto, StockSummaryDto } from './baleApi.dto'

export function toRegisterBatchDto(input: RegisterBatchInput): RegisterBatchDto {
  return {
    shipment_number: normalizeIdentifier(input.shipmentNumber),
    received_at: input.receptionDate,
    provider_name: input.providerName.trim(),
    bales: input.bales.map((bale) => ({
      bale_number: normalizeIdentifier(bale.baleNumber), material_type: normalizeIdentifier(bale.materialType),
      dtex: bale.dtex.trim(), gross_weight_kg: bale.grossWeightKg.trim(), container_weight_kg: bale.containerWeightKg.trim(),
    })),
  }
}

export function toRegisteredBatch(dto: RegisteredBatchDto): RegisteredBatch {
  return { rawMaterialBatchId: dto.raw_material_batch_id, shipmentNumber: dto.shipment_number, receptionDate: dto.received_at, providerName: dto.provider_name, baleCount: dto.bale_count }
}

export function toStockQuery(filters: StockFilters): URLSearchParams {
  const query = new URLSearchParams()
  const values = { received_from: filters.receivedFrom, received_to: filters.receivedTo, shipment_number: filters.shipmentNumber && normalizeIdentifier(filters.shipmentNumber), status: filters.status, provider_name: filters.providerName?.trim(), material_type: filters.materialType && normalizeIdentifier(filters.materialType), dtex: filters.dtex?.trim() }
  for (const [key, value] of Object.entries(values)) if (value) query.set(key, value)
  return query
}

export function toStockSummary(dto: StockSummaryDto): StockSummary {
  return { totalBaleCount: dto.total_bale_count, inWarehouseBaleCount: dto.in_warehouse_bale_count, deliveredBaleCount: dto.delivered_bale_count, totalNetWeightKg: dto.total_net_weight_kg, inWarehouseNetWeightKg: dto.in_warehouse_net_weight_kg, deliveredNetWeightKg: dto.delivered_net_weight_kg }
}

export function toBaleDetail(dto: BaleDetailDto): BaleDetail {
  return { shipmentNumber: dto.shipment_number, baleNumber: dto.bale_number, receptionDate: dto.received_at, providerName: dto.provider_name, materialType: dto.material_type, dtex: dto.dtex, grossWeightKg: dto.gross_weight_kg, containerWeightKg: dto.container_weight_kg, netWeightKg: dto.net_weight_kg, status: dto.status, deliveryDate: dto.delivered_at }
}

export function toDeliverBalesDto(input: DeliveryInput): DeliverBalesDto {
  return { delivery_date: input.deliveryDate, bales: input.bales.map((bale) => ({ shipment_number: normalizeIdentifier(bale.shipmentNumber), bale_number: normalizeIdentifier(bale.baleNumber) })) }
}

export function toDeliveryOutcome(dto: DeliveryOutcomeDto): DeliveryOutcome {
  return { shipmentNumber: dto.shipment_number, baleNumber: dto.bale_number, status: dto.status, error: dto.error ?? undefined }
}

export function toDeliveryResponse(dto: DeliveryResponseDto): DeliveryResponse {
  return { deliveryDate: dto.delivery_date, deliveredCount: dto.delivered_count, failedCount: dto.failed_count, results: dto.results.map(toDeliveryOutcome) }
}
