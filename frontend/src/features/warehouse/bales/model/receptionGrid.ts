import { addDecimals, isDecimal, subtractDecimals } from './decimal'
import type { ReceptionHeader, ReceptionGridRow } from './reception'
import { duplicateReceptionRows, type FieldErrors, validateReceptionRow } from './validation'

export const INITIAL_RECEPTION_ROW_COUNT = 5
export const MAX_RECEPTION_ROWS = 100

export const RECEPTION_EDITABLE_COLUMNS = [
  'baleNumber',
  'materialType',
  'dtex',
  'grossWeightKg',
  'containerWeightKg',
] as const

export type ReceptionEditableColumn = (typeof RECEPTION_EDITABLE_COLUMNS)[number]
export type ReceptionRowStatus = 'empty' | 'partial' | 'valid' | 'invalid'

export interface ReceptionGridState {
  readonly rows: readonly ReceptionGridRow[]
  readonly nextRowId: number
}

export interface ReceptionRowFeedback {
  readonly status: ReceptionRowStatus
  readonly errors: FieldErrors
  readonly isDuplicate: boolean
}

export interface ReceptionSummary {
  readonly contentCount: number
  readonly validCount: number
  readonly errorCount: number
  readonly totalGrossWeightKg: string
  readonly totalContainerWeightKg: string
  readonly totalNetWeightKg: string
}

export interface ReceptionPastePlan {
  readonly accepted: boolean
  readonly state: ReceptionGridState
  readonly reason?: 'capacity' | 'column' | 'shape'
}

export interface ReceptionSubmissionSnapshot {
  readonly header: Readonly<ReceptionHeader>
  readonly bales: readonly Readonly<ReceptionGridRow>[]
}

export function createReceptionGridState(nextRowId = 1): ReceptionGridState {
  return appendEmptyRows({ rows: [], nextRowId }, INITIAL_RECEPTION_ROW_COUNT)
}

export function resetReceptionGrid(state: ReceptionGridState): ReceptionGridState {
  return appendEmptyRows({ rows: [], nextRowId: state.nextRowId }, INITIAL_RECEPTION_ROW_COUNT)
}

export function updateReceptionRows(
  state: ReceptionGridState,
  rows: readonly ReceptionGridRow[],
): ReceptionGridState {
  const normalizedRows = rows.map(withCalculatedNetWeight)
  const nextRowId = Math.max(state.nextRowId, ...normalizedRows.map(rowSequence))
  return ensureContinuationRow({ rows: normalizedRows, nextRowId })
}

export function planReceptionPaste(
  state: ReceptionGridState,
  startRowIndex: number,
  startColumn: ReceptionEditableColumn,
  matrix: readonly (readonly string[])[],
): ReceptionPastePlan {
  if (startRowIndex < 0 || matrix.length === 0 || matrix.some(row => row.length === 0)) {
    return { accepted: false, state, reason: 'shape' }
  }

  const startColumnIndex = RECEPTION_EDITABLE_COLUMNS.indexOf(startColumn)
  if (startColumnIndex === -1 || matrix.some(row => row.length + startColumnIndex > RECEPTION_EDITABLE_COLUMNS.length)) {
    return { accepted: false, state, reason: 'column' }
  }

  const requiredRowCount = startRowIndex + matrix.length
  if (requiredRowCount > MAX_RECEPTION_ROWS) return { accepted: false, state, reason: 'capacity' }

  let candidate = appendEmptyRows(state, requiredRowCount - state.rows.length)
  const pastedRows = candidate.rows.map((row, rowIndex) => {
    const pastedValues = matrix[rowIndex - startRowIndex]
    if (!pastedValues) return row

    const changes = pastedValues.reduce<Partial<ReceptionGridRow>>((result, value, columnOffset) => {
      const column = RECEPTION_EDITABLE_COLUMNS[startColumnIndex + columnOffset]
      result[column] = value
      return result
    }, {})
    return withCalculatedNetWeight({ ...row, ...changes })
  })

  if (pastedRows.filter(isReceptionRowPopulated).length > MAX_RECEPTION_ROWS) {
    return { accepted: false, state, reason: 'capacity' }
  }

  candidate = ensureContinuationRow({ ...candidate, rows: pastedRows })
  return { accepted: true, state: candidate }
}

export function parseSpreadsheetPaste(text: string): readonly (readonly string[])[] {
  return text
    .replace(/\r\n?/g, '\n')
    .replace(/\n$/, '')
    .split('\n')
    .map(row => row.split('\t'))
}

export function getReceptionFeedback(rows: readonly ReceptionGridRow[]): ReadonlyMap<string, ReceptionRowFeedback> {
  const duplicateRows = duplicateReceptionRows(rows)
  return new Map(rows.map(row => {
    const errors = validateReceptionRow(row)
    const populatedFields = editableValues(row).filter(Boolean).length
    const isDuplicate = duplicateRows.has(row.rowId)
    const status: ReceptionRowStatus = populatedFields === 0
      ? 'empty'
      : populatedFields < RECEPTION_EDITABLE_COLUMNS.length
        ? 'partial'
        : Object.keys(errors).length === 0 && !isDuplicate ? 'valid' : 'invalid'
    return [row.rowId, { status, errors, isDuplicate }]
  }))
}

export function validateReceptionHeader(header: ReceptionHeader): FieldErrors {
  const errors: Record<string, string> = {}
  for (const field of ['shipmentNumber', 'receptionDate', 'providerName'] as const) {
    if (!header[field].trim()) errors[field] = 'This field is required.'
  }
  return errors
}

export function isReceptionReadyForSubmission(header: ReceptionHeader, rows: readonly ReceptionGridRow[]): boolean {
  const summary = summarizeReception(rows)
  return Object.keys(validateReceptionHeader(header)).length === 0
    && summary.contentCount > 0
    && summary.errorCount === 0
}

export function summarizeReception(rows: readonly ReceptionGridRow[]): ReceptionSummary {
  const feedback = getReceptionFeedback(rows)
  const populatedRows = rows.filter(isReceptionRowPopulated)
  const validRows = populatedRows.filter(row => feedback.get(row.rowId)?.status === 'valid')
  return {
    contentCount: populatedRows.length,
    validCount: validRows.length,
    errorCount: populatedRows.length - validRows.length,
    totalGrossWeightKg: sumDecimalColumn(validRows, 'grossWeightKg'),
    totalContainerWeightKg: sumDecimalColumn(validRows, 'containerWeightKg'),
    totalNetWeightKg: sumDecimalColumn(validRows, 'netWeightKg'),
  }
}

export function createReceptionSubmissionSnapshot(
  header: ReceptionHeader,
  rows: readonly ReceptionGridRow[],
): ReceptionSubmissionSnapshot {
  return Object.freeze({
    header: Object.freeze({ ...header }),
    bales: Object.freeze(rows.filter(isReceptionRowPopulated).map(row => Object.freeze({ ...row }))),
  })
}

export function isReceptionRowPopulated(row: ReceptionGridRow): boolean {
  return editableValues(row).some(Boolean)
}

function appendEmptyRows(state: ReceptionGridState, count: number): ReceptionGridState {
  if (count <= 0) return state
  const permittedCount = Math.min(count, MAX_RECEPTION_ROWS - state.rows.length)
  const rows = [...state.rows]
  for (let index = 0; index < permittedCount; index += 1) {
    rows.push(emptyReceptionRow(state.nextRowId + index))
  }
  return { rows, nextRowId: state.nextRowId + permittedCount }
}

function ensureContinuationRow(state: ReceptionGridState): ReceptionGridState {
  if (state.rows.length >= MAX_RECEPTION_ROWS || !isReceptionRowPopulated(state.rows.at(-1)!)) return state
  return appendEmptyRows(state, 1)
}

function emptyReceptionRow(sequence: number): ReceptionGridRow {
  return {
    rowId: `reception-row-${sequence}`,
    baleNumber: '',
    materialType: '',
    dtex: '',
    grossWeightKg: '',
    containerWeightKg: '',
    netWeightKg: '',
  }
}

function withCalculatedNetWeight(row: ReceptionGridRow): ReceptionGridRow {
  const grossWeightKg = row.grossWeightKg.trim()
  const containerWeightKg = row.containerWeightKg.trim()
  return {
    ...row,
    netWeightKg: isDecimal(grossWeightKg) && isDecimal(containerWeightKg)
      ? subtractDecimals(grossWeightKg, containerWeightKg)
      : '',
  }
}

function editableValues(row: ReceptionGridRow): readonly string[] {
  return RECEPTION_EDITABLE_COLUMNS.map(column => row[column].trim())
}

function rowSequence(row: ReceptionGridRow): number {
  return Number(row.rowId.replace('reception-row-', '')) + 1
}

function sumDecimalColumn(rows: readonly ReceptionGridRow[], column: 'grossWeightKg' | 'containerWeightKg' | 'netWeightKg'): string {
  return rows.reduce((total, row) => addDecimals(total, row[column]), '0')
}
