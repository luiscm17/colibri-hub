import { httpJson } from '@/api/httpClient'
import type { DeliveryInput, DeliveryOutcome } from '../model/delivery'
import type { RegisterBatchInput, RegisteredBatch } from '../model/reception'
import type { BaleDetail, StockFilters, StockSummary } from '../model/stock'
import { toBaleApiError } from './baleApi.errors'
import type { BaleDetailDto, DeliveryOutcomeDto, RegisteredBatchDto, StockSummaryDto } from './baleApi.dto'
import { toBaleDetail, toDeliverBalesDto, toDeliveryOutcome, toRegisterBatchDto, toRegisteredBatch, toStockQuery, toStockSummary } from './baleApi.mappers'

const BALES_PATH = '/warehouse/bales'

export async function registerBatch(input: RegisterBatchInput, signal?: AbortSignal): Promise<RegisteredBatch> {
  try {
    const response = await httpJson<RegisteredBatchDto>(BALES_PATH, { method: 'POST', body: toRegisterBatchDto(input), signal })
    return toRegisteredBatch(response)
  } catch (error) {
    throw toBaleApiError(error)
  }
}

export async function getStockSummary(filters: StockFilters, signal?: AbortSignal): Promise<StockSummary> {
  try {
    const query = toStockQuery(filters).toString()
    const response = await httpJson<StockSummaryDto>(`${BALES_PATH}${query ? `?${query}` : ''}`, { signal })
    return toStockSummary(response)
  } catch (error) {
    throw toBaleApiError(error)
  }
}

export async function getBaleDetail(shipmentNumber: string, baleNumber: string, signal?: AbortSignal): Promise<BaleDetail> {
  try {
    const response = await httpJson<BaleDetailDto>(`${BALES_PATH}/${encodeURIComponent(shipmentNumber)}/${encodeURIComponent(baleNumber)}`, { signal })
    return toBaleDetail(response)
  } catch (error) {
    throw toBaleApiError(error)
  }
}

export async function deliverBales(input: DeliveryInput, signal?: AbortSignal): Promise<readonly DeliveryOutcome[]> {
  try {
    const response = await httpJson<readonly DeliveryOutcomeDto[]>(`${BALES_PATH}/deliver`, { method: 'POST', body: toDeliverBalesDto(input), signal })
    return response.map(toDeliveryOutcome)
  } catch (error) {
    throw toBaleApiError(error)
  }
}
