import { describe, expect, it } from 'vitest'
import {
  appendProgressRow,
  createProgressDraft,
  isCurrentProgressRequest,
  progressRequestKey,
  replaceProgressRows,
} from './progressModel'

describe('Progress draft', () => {
  it('retains one summary row per machine and yarn-count identity', () => {
    const draft = appendProgressRow(createProgressDraft())
    const rows = replaceProgressRows(draft, [
      { ...draft.rows[0], machineId: 'PSJ-01', yarnCountId: '30/1' },
      { ...draft.rows[1], machineId: 'PSJ-01', yarnCountId: '30/1' },
    ])

    expect(rows.rows).toHaveLength(1)
    expect(rows.rows[0]).toMatchObject({ machineId: 'PSJ-01', yarnCountId: '30/1' })
  })

  it('uses the complete continuity identity as its request key', () => {
    const previous = progressRequestKey({ section: 'preparation', businessDate: '2026-09-01', shift: 'first', machineId: 'PSJ-01', yarnCountId: '30/1' })
    const current = progressRequestKey({ section: 'preparation', businessDate: '2026-09-01', shift: 'first', machineId: 'PSJ-01', yarnCountId: '40/1' })

    expect(previous).not.toBe(current)
    expect(isCurrentProgressRequest(previous, current)).toBe(false)
  })
})
