export type BaleStatus = 'in_warehouse' | 'delivered'

export interface StockFilters {
  receivedFrom?: string
  receivedTo?: string
  shipmentNumber?: string
  status?: BaleStatus
  providerName?: string
  materialType?: string
  dtex?: string
}

export interface StockSummary {
  totalBaleCount: number
  inWarehouseBaleCount: number
  deliveredBaleCount: number
  totalNetWeightKg: string
  inWarehouseNetWeightKg: string
  deliveredNetWeightKg: string
}

export interface BaleDetail {
  id: string
  shipmentNumber: string
  baleNumber: string
  receptionDate: string
  providerName: string
  materialType: string
  dtex: string
  grossWeightKg: string
  containerWeightKg: string
  netWeightKg: string
  status: BaleStatus
  deliveryDate?: string
}
