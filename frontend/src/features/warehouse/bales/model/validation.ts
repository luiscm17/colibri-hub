import { compareDecimals, isDecimal } from './decimal'
import type { DeliveryGridRow } from './delivery'
import type { ReceptionGridRow } from './reception'

export type FieldErrors = Readonly<Record<string, string>>

export function normalizeIdentifier(value: string): string {
  return value.trim().toUpperCase()
}

export function validateReceptionRow(row: ReceptionGridRow): FieldErrors {
  const errors: Record<string, string> = {}
  const values = {
    baleNumber: normalizeIdentifier(row.baleNumber),
    materialType: normalizeIdentifier(row.materialType),
    dtex: row.dtex.trim(),
    grossWeightKg: row.grossWeightKg.trim(),
    containerWeightKg: row.containerWeightKg.trim(),
  }
  const populated = Object.values(values).filter(Boolean).length
  if (populated === 0) return errors

  for (const [field, value] of Object.entries(values)) {
    if (!value) errors[field] = 'This field is required.'
  }
  for (const field of ['dtex', 'grossWeightKg', 'containerWeightKg'] as const) {
    if (values[field] && (!isDecimal(values[field]) || compareDecimals(values[field], '0') <= 0)) {
      errors[field] = 'Enter a positive decimal value.'
    }
  }
  if (!errors.grossWeightKg && !errors.containerWeightKg && compareDecimals(values.grossWeightKg, values.containerWeightKg) <= 0) {
    errors.containerWeightKg = 'Container weight must be lower than gross weight.'
  }
  return errors
}

export function duplicateReceptionRows(rows: readonly ReceptionGridRow[]): ReadonlySet<string> {
  return duplicateRows(rows, (row) => normalizeIdentifier(row.baleNumber), (row) => row.baleNumber.trim() !== '')
}

export function validateDeliveryRows(rows: readonly DeliveryGridRow[]): FieldErrors {
  const errors: Record<string, string> = {}
  for (const row of rows) {
    const shipmentNumber = normalizeIdentifier(row.shipmentNumber)
    const baleNumber = normalizeIdentifier(row.baleNumber)
    if (!shipmentNumber && !baleNumber) continue
    if (!shipmentNumber) errors[`${row.rowId}.shipmentNumber`] = 'Shipment number is required.'
    if (!baleNumber) errors[`${row.rowId}.baleNumber`] = 'Bale number is required.'
  }
  for (const rowId of duplicateRows(rows, (row) => `${normalizeIdentifier(row.shipmentNumber)}:${normalizeIdentifier(row.baleNumber)}`, (row) => Boolean(row.shipmentNumber.trim() && row.baleNumber.trim()))) {
    errors[`${rowId}.identity`] = 'This shipment and bale combination is duplicated.'
  }
  return errors
}

function duplicateRows<T extends { rowId: string }>(rows: readonly T[], keyFor: (row: T) => string, include: (row: T) => boolean): ReadonlySet<string> {
  const idsByKey = new Map<string, string[]>()
  for (const row of rows) {
    if (!include(row)) continue
    const key = keyFor(row)
    idsByKey.set(key, [...(idsByKey.get(key) ?? []), row.rowId])
  }
  return new Set([...idsByKey.values()].filter((ids) => ids.length > 1).flat())
}
