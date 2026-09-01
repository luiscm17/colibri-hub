export const SKEINING_EDITABLE_COLUMNS = ['machine', 'yarnCount', 'skeinQuantity', 'estimatedUnitWeightKg', 'operator', 'observations'] as const

export const SKEINING_COLUMN_LABELS = {
  machine: 'Máquina',
  yarnCount: 'Título del hilo',
  skeinQuantity: 'Cantidad de madejas',
  estimatedUnitWeightKg: 'Peso unitario estimado (kg)',
  operator: 'Operario (opcional)',
  observations: 'Observaciones (opcional)',
  derivedTotalWeightKg: 'Peso total (kg)',
} as const

export type SkeiningColumn = (typeof SKEINING_EDITABLE_COLUMNS)[number]

export type SkeiningRow = Readonly<{
  rowId: string
  machine: string
  yarnCount: string
  skeinQuantity: string
  estimatedUnitWeightKg: string
  operator: string
  observations: string
}>

export type SkeiningDraft = Readonly<{ rows: readonly SkeiningRow[]; nextRowId: number }>

export function createSkeiningDraft(): SkeiningDraft {
  return { rows: [emptyRow(1)], nextRowId: 2 }
}

export function appendSkeiningRow(draft: SkeiningDraft): SkeiningDraft {
  return { rows: [...draft.rows, emptyRow(draft.nextRowId)], nextRowId: draft.nextRowId + 1 }
}

export function replaceSkeiningRows(draft: SkeiningDraft, rows: readonly SkeiningRow[]): SkeiningDraft {
  return { ...draft, rows }
}

export function skeiningRowErrors(row: SkeiningRow): Readonly<Partial<Record<SkeiningColumn, string>>> {
  const values = Object.fromEntries(SKEINING_EDITABLE_COLUMNS.map(column => [column, row[column].trim()])) as Record<SkeiningColumn, string>
  if (!Object.values(values).some(Boolean)) return {}
  const errors: Partial<Record<SkeiningColumn, string>> = {}
  if (!values.machine) errors.machine = 'La máquina es obligatoria.'
  if (!values.yarnCount) errors.yarnCount = 'El título del hilo es obligatorio.'
  if (!values.skeinQuantity) errors.skeinQuantity = 'La cantidad de madejas es obligatoria.'
  if (!values.estimatedUnitWeightKg) errors.estimatedUnitWeightKg = 'El peso unitario estimado es obligatorio.'
  if (values.skeinQuantity && !/^[1-9]\d*$/.test(values.skeinQuantity)) errors.skeinQuantity = 'Ingrese una cantidad entera positiva.'
  if (values.estimatedUnitWeightKg && !/^(?:0|[1-9]\d*)(?:\.\d+)?$/.test(values.estimatedUnitWeightKg)) errors.estimatedUnitWeightKg = 'Ingrese un valor decimal no negativo.'
  return errors
}

function emptyRow(sequence: number): SkeiningRow {
  return { rowId: `skeining-row-${sequence}`, machine: '', yarnCount: '', skeinQuantity: '', estimatedUnitWeightKg: '', operator: '', observations: '' }
}
