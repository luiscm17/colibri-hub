import { describe, expect, it } from 'vitest'
import { SharedRolePermissionGate } from './shared-role-gate'

describe('SharedRolePermissionGate', () => {
  it('binds a normalized non-zero permission replacement and applies it once with the optional reason', () => {
    const gate = new SharedRolePermissionGate(
      { subjectId: 'role-1', subjectVersion: 4, authorityGeneration: '7' },
      [{ action: 'read', scopeId: 'scope-a' }],
      { roleName: 'Operador', description: null },
    )
    const next = [{ action: 'write', scopeId: 'scope-a' }, { action: 'read', scopeId: 'scope-a' }]

    const normalized = [...next].reverse()
    expect(gate.previewRequest(next)).toEqual({ path: '/access/roles/role-1/preview', method: 'POST', body: { permissions: normalized.map(({ action, scopeId }) => ({ action, scope_id: scopeId })) } })
    expect(gate.acceptPreview({ subjectVersion: 4, affectedUserCount: 2 }, [...next].reverse(), gate.currentRequestGeneration())).toBe(true)
    expect(gate.applyRequest('approved')).toEqual({ path: '/access/roles/role-1', method: 'PUT', body: { role_name: 'Operador', description: null, permissions: normalized.map(({ action, scopeId }) => ({ action, scope_id: scopeId })), expected_version: 4, reason: 'approved' } })
    expect(gate.applyRequest('approved')).toBeNull()
  })

  it('blocks zero delta and invalidates stale previews without replaying them', () => {
    const gate = new SharedRolePermissionGate(
      { subjectId: 'role-1', subjectVersion: 4, authorityGeneration: '7' },
      [{ action: 'read', scopeId: 'scope-a' }],
      { roleName: 'Operador', description: null },
    )

    expect(gate.previewRequest([{ action: 'read', scopeId: 'scope-a' }])).toBeNull()
    gate.previewRequest([{ action: 'write', scopeId: 'scope-a' }])
    expect(gate.acceptPreview({ subjectVersion: 4, affectedUserCount: 2 }, [{ action: 'write', scopeId: 'scope-a' }], gate.currentRequestGeneration() + 1)).toBe(false)
    expect(gate.acceptPreview({ subjectVersion: 4, affectedUserCount: 2 }, [{ action: 'write', scopeId: 'scope-a' }], gate.currentRequestGeneration())).toBe(true)
    gate.invalidateFor({ subjectId: 'role-1', subjectVersion: 4, authorityGeneration: '8' })
    expect(gate.applyRequest()).toBeNull()
  })
})
