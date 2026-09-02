import { describe, expect, it } from 'vitest'
import { applyProductionRoster, createDischargeDraft, pasteDischargeRows } from './dischargeModel'

const roster = [
  { id: 'one', number: 1, machine: 'M-01', yarnTitle: '30/1', type: 'Algodón', defaultPackageTareWeightKg: '0.20', defaultCartWeightKg: '1.50', projections: {} },
  { id: 'two', number: 2, machine: 'M-01', yarnTitle: '30/1', type: 'Algodón', defaultPackageTareWeightKg: '0.20', defaultCartWeightKg: '1.50', projections: {} },
] as const

describe('Production roster draft', () => {
  it('preserves repeated production records as distinct roster rows', () => {
    const draft = applyProductionRoster(createDischargeDraft(), roster)
    expect(draft.rows.map(row => row.rowId)).toEqual(['one', 'two'])
    expect(draft.rows.map(row => [row.defaultPackageTareWeightKg, row.defaultCartWeightKg])).toEqual([['0.20', '1.50'], ['0.20', '1.50']])
  })

  it('keeps pasted raw input within the supplied roster', () => {
    const draft = applyProductionRoster(createDischargeDraft(), roster)
    const next = pasteDischargeRows(draft, 'one', 'grossWeightKg', '10\n20\n30')
    expect(next.rows).toHaveLength(2)
    expect(next.rows.map(row => row.grossWeightKg)).toEqual(['10', '20'])
  })
})
