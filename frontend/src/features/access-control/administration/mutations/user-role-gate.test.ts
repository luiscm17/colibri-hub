import { describe, expect, it } from 'vitest'
import { UserRoleReplacementGate } from './user-role-gate'

describe('UserRoleReplacementGate', () => {
  it('binds a non-zero preview to its normalized draft and applies it once', () => {
    const gate = new UserRoleReplacementGate({ subjectId: 'user-1', subjectVersion: 4, authorityGeneration: '7' }, ['role-b', 'role-a'])

    expect(gate.previewRequest(['role-a', 'role-c', 'role-c'])).toEqual({ path: '/access/users/user-1/roles/preview', method: 'POST', body: { role_ids: ['role-a', 'role-c'] } })
    expect(gate.acceptPreview({ subjectVersion: 4, affectedUserCount: 1 }, ['role-c', 'role-a'], gate.currentRequestGeneration())).toBe(true)
    expect(gate.applyRequest()).toEqual({ path: '/access/users/user-1/roles', method: 'PUT', body: { role_ids: ['role-a', 'role-c'], expected_version: 4, reason: '' } })
    expect(gate.applyRequest()).toBeNull()
  })

  it('blocks zero delta and invalidates a preview on edits or authority changes', () => {
    const gate = new UserRoleReplacementGate({ subjectId: 'user-1', subjectVersion: 4, authorityGeneration: '7' }, ['role-a'])

    expect(gate.previewRequest(['role-a'])).toBeNull()
    gate.previewRequest(['role-b'])
    expect(gate.acceptPreview({ subjectVersion: 4, affectedUserCount: 1 }, ['role-b'], gate.currentRequestGeneration())).toBe(true)
    gate.invalidateFor({ subjectId: 'user-1', subjectVersion: 4, authorityGeneration: '8' })
    expect(gate.applyRequest()).toBeNull()
  })
})
