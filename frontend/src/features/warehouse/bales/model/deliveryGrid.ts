import type { DeliveryGridRow, DeliveryInput, DeliveryOutcome } from './delivery'
import { normalizeIdentifier, validateDeliveryRows, type FieldErrors } from './validation'

export const DELIVERY_COLUMNS = ['shipmentNumber', 'baleNumber'] as const
export type DeliveryColumn = (typeof DELIVERY_COLUMNS)[number]
export const MAX_DELIVERY_ROWS = 50
const INITIAL_ROWS = 5

export interface DeliveryGridState { readonly rows: readonly DeliveryGridRow[]; readonly nextRowId: number }
export interface DeliveryFeedback { readonly empty: boolean; readonly duplicate: boolean; readonly errors: FieldErrors }

export function createDeliveryGridState(nextRowId = 1): DeliveryGridState {
  return append({ rows: [], nextRowId }, INITIAL_ROWS)
}

export function resetDeliveryGrid(state: DeliveryGridState): DeliveryGridState {
  return append({ rows: [], nextRowId: state.nextRowId }, INITIAL_ROWS)
}

export function updateDeliveryRows(state: DeliveryGridState, rows: readonly DeliveryGridRow[]): DeliveryGridState {
  const locked = new Map(state.rows.filter(row => row.result === 'delivered').map(row => [row.rowId, row]))
  const nextRows = rows.map(row => locked.get(row.rowId) ?? row)
  return continuation({ rows: nextRows, nextRowId: Math.max(state.nextRowId, ...nextRows.map(sequence)) })
}

export function planDeliveryPaste(state: DeliveryGridState, startRow: number, startColumn: DeliveryColumn, matrix: readonly (readonly string[])[]) {
  const columnIndex = DELIVERY_COLUMNS.indexOf(startColumn)
  if (startRow < 0 || columnIndex < 0 || matrix.length === 0 || matrix.some(row => row.length === 0 || row.length + columnIndex > DELIVERY_COLUMNS.length)) return { accepted: false, state }
  if (startRow + matrix.length > MAX_DELIVERY_ROWS) return { accepted: false, state }
  let candidate = append(state, startRow + matrix.length - state.rows.length)
  if (matrix.some((_, index) => candidate.rows[startRow + index]?.result === 'delivered')) return { accepted: false, state }
  const rows = candidate.rows.map((row, index) => {
    const values = matrix[index - startRow]
    if (!values) return row
    return values.reduce<DeliveryGridRow>((next, value, offset) => ({ ...next, [DELIVERY_COLUMNS[columnIndex + offset]]: value }), row)
  })
  if (rows.filter(populated).length > MAX_DELIVERY_ROWS) return { accepted: false, state }
  candidate = continuation({ ...candidate, rows })
  return { accepted: true, state: candidate }
}

export function parseDeliveryPaste(value: string) { return value.replace(/\r\n?/g, '\n').replace(/\n$/, '').split('\n').map(row => row.split('\t')) }
export function feedbackFor(rows: readonly DeliveryGridRow[]): ReadonlyMap<string, DeliveryFeedback> {
  const errors = validateDeliveryRows(rows)
  return new Map(rows.map(row => [row.rowId, { empty: !populated(row), duplicate: Boolean(errors[`${row.rowId}.identity`]), errors }]))
}
export function readyForDelivery(date: string, rows: readonly DeliveryGridRow[]) { return Boolean(date) && rows.some(row => populated(row) && row.result !== 'delivered') && Object.keys(validateDeliveryRows(rows)).length === 0 }
export function deliverySnapshot(date: string, rows: readonly DeliveryGridRow[]): DeliveryInput {
  return { deliveryDate: date, bales: rows.filter(row => populated(row) && row.result !== 'delivered').map(row => ({ rowId: row.rowId, shipmentNumber: row.shipmentNumber, baleNumber: row.baleNumber })) }
}
export function applyDeliveryOutcomes(rows: readonly DeliveryGridRow[], outcomes: readonly DeliveryOutcome[]) {
  const outcomesByIdentity = new Map(outcomes.map(outcome => [`${normalizeIdentifier(outcome.shipmentNumber)}:${normalizeIdentifier(outcome.baleNumber)}`, outcome]))
  return rows.map(row => {
    const outcome = outcomesByIdentity.get(`${normalizeIdentifier(row.shipmentNumber)}:${normalizeIdentifier(row.baleNumber)}`)
    return outcome ? { ...row, result: outcome.status, resultMessage: outcome.error?.message } : row
  })
}
function populated(row: DeliveryGridRow) { return Boolean(row.shipmentNumber.trim() || row.baleNumber.trim()) }
function append(state: DeliveryGridState, count: number): DeliveryGridState { return count <= 0 ? state : append({ rows: [...state.rows, ...Array.from({ length: count }, (_, index) => empty(state.nextRowId + index))], nextRowId: state.nextRowId + count }, 0) }
function continuation(state: DeliveryGridState): DeliveryGridState { return state.rows.length < MAX_DELIVERY_ROWS && populated(state.rows.at(-1)!) ? append(state, 1) : state }
function empty(id: number): DeliveryGridRow { return { rowId: `delivery-${id}`, shipmentNumber: '', baleNumber: '', result: 'pending' } }
function sequence(row: DeliveryGridRow) { return Number(row.rowId.replace('delivery-', '')) || 0 }
