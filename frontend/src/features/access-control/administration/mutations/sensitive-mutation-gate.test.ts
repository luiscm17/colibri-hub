import { describe, expect, it } from 'vitest'
import { SensitiveMutationGate, normalizedRoleIds } from './sensitive-mutation-gate'

describe('SensitiveMutationGate', () => {
  const subject = { subjectId: 'user-1', subjectVersion: 4, authorityGeneration: '7' }

  it('normalizes the fingerprint and blocks a semantic no-op', () => {
    expect(normalizedRoleIds([' role-b ', 'role-a', 'role-a'])).toEqual(['role-a', 'role-b'])
    const gate = new SensitiveMutationGate('user-role-replacement', subject, ['role-a'])

    expect(gate.beginPreview(['role-a'], '')).toBeNull()
  })

  it('invalidates reason edits, aborts stale previews, and accepts only the latest version', () => {
    const gate = new SensitiveMutationGate('user-role-replacement', subject, ['role-a'])
    const first = gate.beginPreview(['role-b'], '')!
    gate.invalidate()
    expect(first.signal.aborted).toBe(true)
    expect(gate.acceptPreview({ subjectVersion: 4 }, ['role-b'], '', first.generation)).toBe(false)

    const latest = gate.beginPreview(['role-b'], 'reviewed')!
    expect(gate.acceptPreview({ subjectVersion: 4 }, ['role-b'], 'reviewed', latest.generation)).toBe(true)
    gate.invalidateForReason('changed')
    expect(gate.confirm()).toBe(false)
  })

  it('requires explicit confirmation, emits one apply, and clears safely for access loss or conflict', () => {
    const gate = new SensitiveMutationGate('user-role-replacement', subject, ['role-a'])
    const preview = gate.beginPreview(['role-b'], '')!
    expect(gate.acceptPreview({ subjectVersion: 4 }, ['role-b'], '', preview.generation)).toBe(true)
    expect(gate.beginApply()).toBeNull()
    expect(gate.confirm()).toBe(true)
    expect(gate.beginApply()).toEqual({ draft: ['role-b'], version: 4, reason: '' })
    expect(gate.beginApply()).toBeNull()

    gate.handleOutcome('access_version_conflict')
    expect(gate.confirm()).toBe(false)
    gate.handleOutcome('401')
    expect(gate.hasProtectedState()).toBe(false)
  })
})
