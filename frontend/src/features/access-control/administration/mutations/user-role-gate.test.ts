import { describe, expect, it } from 'vitest'
import { UserRoleReplacementGate } from './user-role-gate'

describe('UserRoleReplacementGate', () => {
  it('binds a non-zero preview to its normalized draft and applies it once', () => {
    const gate = new UserRoleReplacementGate({ subjectId: 'user-1', subjectVersion: 4, authorityGeneration: '7' }, ['role-b', 'role-a'])

    expect(gate.previewRequest(['role-a', 'role-c', 'role-c'])).toEqual({ path: '/access/users/user-1/roles/preview', method: 'POST', body: { role_ids: ['role-a', 'role-c'] } })
    expect(gate.acceptPreview({ subjectVersion: 4, affectedUserCount: 1 }, ['role-c', 'role-a'], gate.currentRequestGeneration())).toBe(true)
    expect(gate.applyRequest()).toBeNull()
    expect(gate.confirm()).toBe(true)
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

  it('binds the optional reason to the previewed apply request', () => {
    const gate = new UserRoleReplacementGate({ subjectId: 'user-1', subjectVersion: 4, authorityGeneration: '7' }, ['role-a'])
    gate.previewRequest(['role-b'], 'reviewed')
    expect(gate.acceptPreview({ subjectVersion: 4, affectedUserCount: 1 }, ['role-b'], gate.currentRequestGeneration(), 'reviewed')).toBe(true)
    expect(gate.confirm()).toBe(true)
    expect(gate.applyRequest()?.body).toMatchObject({ reason: 'reviewed' })
  })

  it('suppresses duplicate previews while the same preview is pending', () => {
    const gate = new UserRoleReplacementGate({ subjectId: 'user-1', subjectVersion: 4, authorityGeneration: '7' }, ['role-a'])

    expect(gate.previewRequest(['role-b'])).not.toBeNull()
    expect(gate.previewRequest(['role-b'])).toBeNull()
    expect(gate.currentRequestGeneration()).toBe(1)
  })
})
