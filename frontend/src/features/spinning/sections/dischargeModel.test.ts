import { describe, expect, it } from 'vitest'
import { applyProductionRoster, createDischargeDraft, pasteDischargeRows, productionRowState } from './dischargeModel'

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

  it('marks malformed pasted numeric input as locally invalid without calculating an outcome', () => {
    const draft = applyProductionRoster(createDischargeDraft(), roster)
    const next = pasteDischargeRows(draft, 'one', 'grossWeightKg', 'not-a-number')

    expect(productionRowState(next.rows[0], 'ringSpinning')).toBe('invalid')
    expect(next.rows[0].projections).toEqual({})
  })

  it('distinguishes pending, complete, and acknowledged no-production local entry states', () => {
    const row = applyProductionRoster(createDischargeDraft(), roster).rows[0]

    expect(productionRowState(row, 'ringSpinning')).toBe('pending')
    expect(productionRowState({ ...row, grossWeightKg: '10', spindleCount: '20', packageTareWeightG: '5', cartWeightKg: '1' }, 'ringSpinning')).toBe('complete')
    expect(productionRowState({ ...row, grossWeightKg: '0', spindleCount: '0', packageTareWeightG: '0', cartWeightKg: '0' }, 'ringSpinning')).toBe('acknowledged-no-production')
  })
})
