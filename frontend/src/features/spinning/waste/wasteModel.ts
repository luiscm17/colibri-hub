import type { WasteCaptureRecord } from '../integration/contracts'

export type WasteRow = Readonly<{
  rowId: string
  number: number
  section: string
  machine: string
  weightKg: string
}>

export type WasteDraft = Readonly<{ rows: readonly WasteRow[] }>

export function createWasteDraft(records: readonly WasteCaptureRecord[] = []): WasteDraft {
  return { rows: records.map(record => ({ rowId: record.id, number: record.number, section: record.section, machine: record.machine, weightKg: record.weightKg })) }
}

export function replaceWasteRows(draft: WasteDraft, rows: readonly WasteRow[]): WasteDraft {
  return { ...draft, rows }
}
