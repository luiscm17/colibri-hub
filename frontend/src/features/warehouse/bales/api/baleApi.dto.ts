export interface RegisterBatchDto {
  shipment_number: string
  received_at: string
  provider_name: string
  bales: readonly ReceivedBaleDto[]
}

export interface ReceivedBaleDto {
  bale_number: string
  material_type: string
  dtex: string
  gross_weight_kg: string
  container_weight_kg: string
}

export interface RegisteredBatchDto {
  raw_material_batch_id: string
  shipment_number: string
  received_at: string
  provider_name: string
  bale_count: number
}

export interface StockSummaryDto {
  total_bale_count: number
  in_warehouse_bale_count: number
  delivered_bale_count: number
  total_net_weight_kg: string
  in_warehouse_net_weight_kg: string
  delivered_net_weight_kg: string
}

export interface BaleDetailDto {
  shipment_number: string
  bale_number: string
  received_at: string
  provider_name: string
  material_type: string
  dtex: string
  gross_weight_kg: string
  container_weight_kg: string
  net_weight_kg: string
  status: 'in_warehouse' | 'delivered'
  delivered_at?: string
}

export interface DeliverBalesDto {
  delivery_date: string
  bales: readonly BaleIdentityDto[]
}

export interface BaleIdentityDto {
  shipment_number: string
  bale_number: string
}

export interface DeliveryOutcomeDto extends BaleIdentityDto {
  result: 'delivered' | 'already_delivered' | 'not_found'
  message?: string
}
