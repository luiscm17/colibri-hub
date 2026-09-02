import type { ProductionRosterEntry } from '../integration/contracts'
import type { SpinningWorkspace } from '../workspaces'

export type DischargeColumn = 'grossWeightKg' | 'spindleCount' | 'packageTareWeightG' | 'cartWeightKg' | 'skeinQuantity' | 'skeinUnitWeightG' | 'operator' | 'observations'

export type ProductionDischargeRow = Readonly<{
  rowId: string
  number: number
  machine: string
  yarnTitle: string
  type: string
  defaultPackageTareWeightKg: string
  defaultCartWeightKg: string
  projections: Readonly<Record<string, string | null>>
  grossWeightKg: string
  spindleCount: string
  packageTareWeightG: string
  cartWeightKg: string
  skeinQuantity: string
  skeinUnitWeightG: string
  operator: string
  observations: string
}>

export type ProductionDischargeDraft = Readonly<{
  rows: readonly ProductionDischargeRow[]
}>

export type ProductionRowState = 'pending' | 'invalid' | 'complete' | 'acknowledged-no-production'

export function createDischargeDraft(): ProductionDischargeDraft {
  return { rows: [] }
}

export function replaceDischargeRows(_draft: ProductionDischargeDraft, rows: readonly ProductionDischargeRow[]): ProductionDischargeDraft {
  return { rows }
}

export function applyProductionRoster(draft: ProductionDischargeDraft, roster: readonly ProductionRosterEntry[]): ProductionDischargeDraft {
  const existing = new Map(draft.rows.map(row => [row.rowId, row]))
  return { rows: roster.map(entry => ({ ...emptyRow(entry), ...existing.get(entry.id), rowId: entry.id, number: entry.number, machine: entry.machine, yarnTitle: entry.yarnTitle, type: entry.type, defaultPackageTareWeightKg: entry.defaultPackageTareWeightKg, defaultCartWeightKg: entry.defaultCartWeightKg, projections: entry.projections })) }
}

export function pasteDischargeRows(
  draft: ProductionDischargeDraft,
  rowId: string,
  column: DischargeColumn,
  text: string,
): ProductionDischargeDraft {
  const startRow = draft.rows.findIndex(row => row.rowId === rowId)
  if (startRow < 0) return draft
  const startColumn = DISCHARGE_EDITABLE_COLUMNS.indexOf(column)
  if (startColumn < 0) return draft
  let rows = [...draft.rows]
  for (const [offset, values] of text.replace(/\r/g, '').split('\n').filter(Boolean).map(line => line.split('\t')).entries()) {
    const row = rows[startRow + offset]
    if (!row) break
    const patch = Object.fromEntries(values.slice(0, DISCHARGE_EDITABLE_COLUMNS.length - startColumn).map((value, index) => [DISCHARGE_EDITABLE_COLUMNS[startColumn + index], value]))
    rows = rows.map(candidate => candidate.rowId === row.rowId ? { ...candidate, ...patch } : candidate)
  }
  return { rows }
}

export const DISCHARGE_EDITABLE_COLUMNS: readonly DischargeColumn[] = ['grossWeightKg', 'spindleCount', 'packageTareWeightG', 'cartWeightKg', 'skeinQuantity', 'skeinUnitWeightG', 'operator', 'observations']

const decimalPattern = /^\d+(?:[.,]\d+)?$/
const wholeNumberPattern = /^\d+$/
const zeroPattern = /^0(?:[.,]0+)?$/

export function productionRowState(row: ProductionDischargeRow, workspace: SpinningWorkspace): ProductionRowState {
  const fields = workspace === 'preparation'
    ? [{ value: row.grossWeightKg, pattern: decimalPattern }, { value: row.spindleCount, pattern: wholeNumberPattern }]
    : workspace === 'skeining'
      ? [{ value: row.skeinQuantity, pattern: wholeNumberPattern }, { value: row.skeinUnitWeightG, pattern: decimalPattern }]
      : [{ value: row.grossWeightKg, pattern: decimalPattern }, { value: row.spindleCount, pattern: wholeNumberPattern }, { value: row.packageTareWeightG, pattern: decimalPattern }, { value: row.cartWeightKg, pattern: decimalPattern }]

  if (fields.some(({ value, pattern }) => value !== '' && !pattern.test(value))) return 'invalid'
  if (fields.every(({ value }) => value === '')) return 'pending'
  if (fields.every(({ value }) => zeroPattern.test(value))) return 'acknowledged-no-production'
  return fields.every(({ value, pattern }) => pattern.test(value)) ? 'complete' : 'pending'
}

function emptyRow(entry: ProductionRosterEntry): ProductionDischargeRow {
  return { rowId: entry.id, number: entry.number, machine: entry.machine, yarnTitle: entry.yarnTitle, type: entry.type, defaultPackageTareWeightKg: entry.defaultPackageTareWeightKg, defaultCartWeightKg: entry.defaultCartWeightKg, projections: entry.projections, grossWeightKg: '', spindleCount: '', packageTareWeightG: '', cartWeightKg: '', skeinQuantity: '', skeinUnitWeightG: '', operator: '', observations: '' }
}
