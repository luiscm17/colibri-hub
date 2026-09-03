import type { ProgressIdentity } from '../integration/contracts'
import type { ProgressRosterEntry } from '../integration/contracts'

export type ProgressRow = Readonly<{ rowId: string; number: number; machine: string; yarnTitle: string; type: string; projections: Readonly<Record<string, string | null>>; grossWeightG: string; tareWeightG: string; spindleCount: string; inputWeightKg: string; outputWeightKg: string; dischargeWeightKg: string; hours: string; observations: string }>
export type ProgressDraft = Readonly<{ rows: readonly ProgressRow[] }>

export function createProgressDraft(): ProgressDraft {
  return { rows: [] }
}

export function replaceProgressRows(_draft: ProgressDraft, rows: readonly ProgressRow[]): ProgressDraft {
  return { rows }
}

export function applyProgressRoster(draft: ProgressDraft, roster: readonly ProgressRosterEntry[]): ProgressDraft {
  const existing = new Map(draft.rows.map(row => [row.rowId, row]))
  return { rows: roster.map(entry => ({ ...emptyRow(entry), ...existing.get(entry.id), rowId: entry.id, number: entry.number, machine: entry.machine, yarnTitle: entry.yarnTitle, type: entry.type, projections: entry.projections })) }
}

export function progressRequestKey(identity: ProgressIdentity): string {
  return [identity.section, identity.businessDate, identity.shift, identity.machineId, identity.yarnCountId].join('\u0000')
}

export function isCurrentProgressRequest(requestKey: string, currentKey: string | undefined): boolean {
  return requestKey === currentKey
}

function emptyRow(entry: ProgressRosterEntry): ProgressRow {
  return { rowId: entry.id, number: entry.number, machine: entry.machine, yarnTitle: entry.yarnTitle, type: entry.type, projections: entry.projections, grossWeightG: '', tareWeightG: '', spindleCount: '', inputWeightKg: '', outputWeightKg: '', dischargeWeightKg: '', hours: '', observations: '' }
}
