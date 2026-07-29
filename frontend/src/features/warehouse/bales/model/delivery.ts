export type DeliveryResult = 'pending' | 'delivered' | 'already_delivered' | 'not_found' | 'error'

export interface DeliveryGridRow {
  rowId: string
  shipmentNumber: string
  baleNumber: string
  result: DeliveryResult
  resultMessage?: string
}

export interface DeliveryInput {
  deliveryDate: string
  bales: readonly Pick<DeliveryGridRow, 'rowId' | 'shipmentNumber' | 'baleNumber'>[]
}

export interface DeliveryOutcome {
  shipmentNumber: string
  baleNumber: string
  status: Exclude<DeliveryResult, 'pending' | 'error'>
  error?: { readonly code: string; readonly message: string }
}

export interface DeliveryResponse {
  deliveryDate: string
  deliveredCount: number
  failedCount: number
  results: readonly DeliveryOutcome[]
}
