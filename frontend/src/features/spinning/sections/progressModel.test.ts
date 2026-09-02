import { describe, expect, it } from 'vitest'
import { applyProgressRoster, createProgressDraft, replaceProgressRows } from './progressModel'

const roster = [
  { id: 'one', number: 1, machine: 'M-01', yarnTitle: '30/1', type: 'Algodón', projections: {} },
  { id: 'two', number: 2, machine: 'M-01', yarnTitle: '30/1', type: 'Algodón', projections: {} },
] as const

describe('Progress roster draft', () => {
  it('retains repeated roster rows with the same machine and title', () => {
    const draft = applyProgressRoster(createProgressDraft(), roster)
    expect(draft.rows.map(row => row.rowId)).toEqual(['one', 'two'])
    expect(replaceProgressRows(draft, draft.rows)).toEqual(draft)
  })
})
