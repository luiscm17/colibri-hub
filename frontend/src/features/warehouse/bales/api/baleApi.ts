import { httpJson } from '@/api/httpClient'
import type { DeliveryInput, DeliveryResponse } from '../model/delivery'
import type { RegisterBatchInput, RegisteredBatch } from '../model/reception'
import type { BaleDetail, StockFilters, StockSummary } from '../model/stock'
import { toBaleApiError } from './baleApi.errors'
import type { BaleDetailDto, DeliveryResponseDto, RegisteredBatchDto, StockSummaryDto } from './baleApi.dto'
import { toBaleDetail, toDeliverBalesDto, toDeliveryResponse, toRegisterBatchDto, toRegisteredBatch, toStockQuery, toStockSummary } from './baleApi.mappers'

const BALES_PATH = '/warehouse/bales'

export async function registerBatch(input: RegisterBatchInput, signal?: AbortSignal): Promise<RegisteredBatch> {
  try {
    const response = await httpJson<RegisteredBatchDto>(BALES_PATH, { method: 'POST', body: toRegisterBatchDto(input), signal, recoverAccessDenied: true })
    return toRegisteredBatch(response)
  } catch (error) {
    throw toBaleApiError(error)
  }
}

export async function getStockSummary(filters: StockFilters, signal?: AbortSignal): Promise<StockSummary> {
  try {
    const query = toStockQuery(filters).toString()
    const response = await httpJson<StockSummaryDto>(`${BALES_PATH}${query ? `?${query}` : ''}`, { signal, recoverAccessDenied: true })
    return toStockSummary(response)
  } catch (error) {
    throw toBaleApiError(error)
  }
}

export async function getBaleDetail(shipmentNumber: string, baleNumber: string, signal?: AbortSignal): Promise<BaleDetail> {
  try {
    const response = await httpJson<BaleDetailDto>(`${BALES_PATH}/${encodeURIComponent(shipmentNumber)}/${encodeURIComponent(baleNumber)}`, { signal, recoverAccessDenied: true })
    return toBaleDetail(response)
  } catch (error) {
    throw toBaleApiError(error)
  }
}

export async function deliverBales(input: DeliveryInput, signal?: AbortSignal): Promise<DeliveryResponse> {
  try {
    const response = await httpJson<DeliveryResponseDto>(`${BALES_PATH}/deliver`, { method: 'POST', body: toDeliverBalesDto(input), signal, recoverAccessDenied: true })
    return toDeliveryResponse(response)
  } catch (error) {
    throw toBaleApiError(error)
  }
}
