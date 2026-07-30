export interface ReceptionHeader {
  shipmentNumber: string
  receptionDate: string
  providerName: string
}

export interface ReceptionGridRow {
  rowId: string
  baleNumber: string
  materialType: string
  dtex: string
  grossWeightKg: string
  containerWeightKg: string
  netWeightKg: string
}

export interface RegisterBatchInput extends ReceptionHeader {
  bales: readonly ReceptionGridRow[]
}

export interface RegisteredBatch {
  rawMaterialBatchId: string
  shipmentNumber: string
  receptionDate: string
  providerName: string
  baleCount: number
}
