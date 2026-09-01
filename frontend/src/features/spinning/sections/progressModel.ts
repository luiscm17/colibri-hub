import type { ProgressIdentity } from '../integration/contracts'

export type ProgressRow = Readonly<{ rowId: string; machineId: string; yarnCountId: string }>
export type ProgressDraft = Readonly<{ rows: readonly ProgressRow[]; nextRowId: number }>

export function createProgressDraft(): ProgressDraft {
  return { rows: [emptyRow(1)], nextRowId: 2 }
}

export function appendProgressRow(draft: ProgressDraft): ProgressDraft {
  return { rows: [...draft.rows, emptyRow(draft.nextRowId)], nextRowId: draft.nextRowId + 1 }
}

export function replaceProgressRows(draft: ProgressDraft, rows: readonly ProgressRow[]): ProgressDraft {
  const seen = new Set<string>()
  const uniqueRows = rows.filter(row => {
    const key = row.machineId && row.yarnCountId ? `${row.machineId}\u0000${row.yarnCountId}` : row.rowId
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
  return { ...draft, rows: uniqueRows }
}

export function progressRequestKey(identity: ProgressIdentity): string {
  return [identity.section, identity.businessDate, identity.shift, identity.machineId, identity.yarnCountId].join('\u0000')
}

export function isCurrentProgressRequest(requestKey: string, currentKey: string | undefined): boolean {
  return requestKey === currentKey
}

function emptyRow(sequence: number): ProgressRow {
  return { rowId: `progress-row-${sequence}`, machineId: '', yarnCountId: '' }
}
