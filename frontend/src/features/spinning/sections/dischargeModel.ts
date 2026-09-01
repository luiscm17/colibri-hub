export const DISCHARGE_EDITABLE_COLUMNS = [
  'machine', 'yarnCount', 'grossWeightKg', 'operativeSpindleCount', 'spindleTareWeightG', 'cartWeightKg', 'rovingCount', 'observations',
] as const
export const DISCHARGE_COLUMN_LABELS = {
  machine: 'Máquina', yarnCount: 'Título del hilo', grossWeightKg: 'Peso bruto (kg)', operativeSpindleCount: 'Cantidad de husos operativos',
  spindleTareWeightG: 'Peso de tara del huso (g)', cartWeightKg: 'Peso del carro (kg)', rovingCount: 'Título de mecha (opcional)', observations: 'Observaciones (opcional)',
  netWeight: 'Peso neto (kg)',
} as const

export type DischargeColumn = (typeof DISCHARGE_EDITABLE_COLUMNS)[number]
export type GridRowState = 'pending' | 'invalid' | 'complete' | 'acknowledged-no-production'

export type ProductionDischargeRow = Readonly<{
  rowId: string
  machine: string
  yarnCount: string
  grossWeightKg: string
  operativeSpindleCount: string
  spindleTareWeightG: string
  cartWeightKg: string
  rovingCount: string
  observations: string
}>

export type ProductionDischargeDraft = Readonly<{
  rows: readonly ProductionDischargeRow[]
  nextRowId: number
}>

export type DischargeRowFeedback = Readonly<{
  state: GridRowState
  errors: Readonly<Partial<Record<DischargeColumn, string>>>
}>

export function createDischargeDraft(): ProductionDischargeDraft {
  return { rows: [emptyRow(1)], nextRowId: 2 }
}

export function appendDischargeRow(draft: ProductionDischargeDraft): ProductionDischargeDraft {
  return { rows: [...draft.rows, emptyRow(draft.nextRowId)], nextRowId: draft.nextRowId + 1 }
}

export function replaceDischargeRows(draft: ProductionDischargeDraft, rows: readonly ProductionDischargeRow[]): ProductionDischargeDraft {
  return { ...draft, rows }
}

export function pasteDischargeRows(
  draft: ProductionDischargeDraft,
  rowId: string,
  column: DischargeColumn,
  text: string,
): ProductionDischargeDraft {
  const startRow = draft.rows.findIndex(row => row.rowId === rowId)
  if (startRow < 0) return draft
  let next = draft
  const startColumn = DISCHARGE_EDITABLE_COLUMNS.indexOf(column)
  for (const [offset, values] of text.replace(/\r/g, '').split('\n').filter(Boolean).map(line => line.split('\t')).entries()) {
    while (startRow + offset >= next.rows.length) next = appendDischargeRow(next)
    const row = next.rows[startRow + offset]
    const patch = Object.fromEntries(values.slice(0, DISCHARGE_EDITABLE_COLUMNS.length - startColumn).map((value, index) => [DISCHARGE_EDITABLE_COLUMNS[startColumn + index], value]))
    next = replaceDischargeRows(next, next.rows.map(candidate => candidate.rowId === row.rowId ? { ...candidate, ...patch } : candidate))
  }
  return next
}

export function dischargeRowFeedback(row: ProductionDischargeRow): DischargeRowFeedback {
  const values = {
    machine: row.machine.trim(), yarnCount: row.yarnCount.trim(), grossWeightKg: row.grossWeightKg.trim(),
    operativeSpindleCount: row.operativeSpindleCount.trim(), spindleTareWeightG: row.spindleTareWeightG.trim(),
    cartWeightKg: row.cartWeightKg.trim(), rovingCount: row.rovingCount.trim(), observations: row.observations.trim(),
  }
  if (!Object.values(values).some(Boolean)) return { state: 'pending', errors: {} }
  const errors: Partial<Record<DischargeColumn, string>> = {}
  if (!values.machine) errors.machine = 'La máquina es obligatoria.'
  if (!values.yarnCount) errors.yarnCount = 'El título del hilo es obligatorio.'
  if (!values.grossWeightKg) errors.grossWeightKg = 'El peso bruto es obligatorio.'
  if (!values.operativeSpindleCount) errors.operativeSpindleCount = 'La cantidad de husos operativos es obligatoria.'
  if (!values.spindleTareWeightG) errors.spindleTareWeightG = 'El peso de tara del huso es obligatorio.'
  if (!values.cartWeightKg) errors.cartWeightKg = 'El peso del carro es obligatorio.'
  for (const field of ['grossWeightKg', 'spindleTareWeightG', 'cartWeightKg'] as const) {
    if (values[field] && !/^(?:0|[1-9]\d*)(?:\.\d+)?$/.test(values[field])) errors[field] = 'Ingrese un valor decimal no negativo.'
  }
  for (const field of ['operativeSpindleCount', 'rovingCount'] as const) {
    if (values[field] && !/^(?:0|[1-9]\d*)$/.test(values[field])) errors[field] = 'Ingrese un número entero no negativo.'
  }
  if (Object.keys(errors).length) return { state: 'invalid', errors }
  return { state: values.grossWeightKg === '0' ? 'acknowledged-no-production' : 'complete', errors }
}

function emptyRow(sequence: number): ProductionDischargeRow {
  return { rowId: `discharge-row-${sequence}`, machine: '', yarnCount: '', grossWeightKg: '', operativeSpindleCount: '', spindleTareWeightG: '', cartWeightKg: '', rovingCount: '', observations: '' }
}
