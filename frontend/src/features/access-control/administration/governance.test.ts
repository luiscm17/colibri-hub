import { describe, expect, it } from 'vitest'
import { MutationGate } from './governance'

describe('governance mutation gate', () => {
  it('blocks a duplicate fingerprint and clears it when the submission ends', () => {
    const gate = new MutationGate()
    expect(gate.tryStart('users:u1:1')).toBe(true)
    expect(gate.tryStart('users:u1:1')).toBe(false)
    gate.finish('users:u1:1')
    expect(gate.tryStart('users:u1:1')).toBe(true)
  })
  it('requires a fresh preview after a draft, conflict, or authority invalidation', () => {
    const gate = new MutationGate()
    gate.setPreview('roles:r1:2', 2)
    expect(gate.canConfirm('roles:r1:2', 2)).toBe(true)
    gate.invalidatePreview()
    expect(gate.canConfirm('roles:r1:2', 2)).toBe(false)
  })
  it('maps backend concurrency and last-administrator rejections without retrying', () => {
    expect(MutationGate.recovery('access_version_conflict')).toBe('reload')
    expect(MutationGate.recovery('last_system_administrator_required')).toBe('last-administrator')
    expect(MutationGate.recovery('access_denied')).toBe('clear')
  })
})
