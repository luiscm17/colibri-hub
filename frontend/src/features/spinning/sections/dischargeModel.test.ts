import { describe, expect, it } from 'vitest'
import {
  appendDischargeRow,
  createDischargeDraft,
  DISCHARGE_COLUMN_LABELS,
  DISCHARGE_EDITABLE_COLUMNS,
  dischargeRowFeedback,
  pasteDischargeRows,
} from './dischargeModel'

describe('Production Discharge draft', () => {
  it('defines all captured units and omits direct net-weight input', () => {
    expect(DISCHARGE_EDITABLE_COLUMNS).toEqual(['machine', 'yarnCount', 'grossWeightKg', 'operativeSpindleCount', 'spindleTareWeightG', 'cartWeightKg', 'rovingCount', 'observations'])
    expect(DISCHARGE_COLUMN_LABELS).toMatchObject({ grossWeightKg: 'Peso bruto (kg)', spindleTareWeightG: 'Peso de tara del huso (g)', cartWeightKg: 'Peso del carro (kg)', rovingCount: 'Título de mecha (opcional)', observations: 'Observaciones (opcional)', netWeight: 'Peso neto (kg)' })
    expect(DISCHARGE_EDITABLE_COLUMNS).not.toContain('netWeight')
  })
  it('keeps repeated machine and yarn-count discharges as distinct immutable events', () => {
    const first = createDischargeDraft()
    const second = appendDischargeRow(first)
    const rows = second.rows.map(row => ({ ...row, machine: 'machine-a', yarnCount: 'count-a', grossWeightKg: '14.5', operativeSpindleCount: '100', spindleTareWeightG: '4.5', cartWeightKg: '1.5' }))

    expect(rows).toHaveLength(2)
    expect(rows.map(row => row.rowId)).toEqual(['discharge-row-1', 'discharge-row-2'])
    expect(dischargeRowFeedback(rows[0]).state).toBe('complete')
    expect(dischargeRowFeedback(rows[1]).state).toBe('complete')
  })

  it('keeps malformed pasted discharge data and optional fields in the affected local row', () => {
    const draft = createDischargeDraft()
    const next = pasteDischargeRows(draft, draft.rows[0].rowId, 'machine', 'machine-a\tcount-a\tinvalid\t100\t4.5\t1.5\t8\tShift note')

    expect(next.rows).toHaveLength(1)
    expect(next.rows[0]).toMatchObject({ machine: 'machine-a', yarnCount: 'count-a', grossWeightKg: 'invalid', rovingCount: '8', observations: 'Shift note' })
    expect(dischargeRowFeedback(next.rows[0])).toMatchObject({ state: 'invalid', errors: { grossWeightKg: 'Ingrese un valor decimal no negativo.' } })
  })

  it('recognizes a raw zero discharge acknowledgement without calculating net weight', () => {
    const row = { ...createDischargeDraft().rows[0], machine: 'machine-a', yarnCount: 'count-a', grossWeightKg: '0', operativeSpindleCount: '0', spindleTareWeightG: '0', cartWeightKg: '0' }

    expect(dischargeRowFeedback(row).state).toBe('acknowledged-no-production')
  })
})
