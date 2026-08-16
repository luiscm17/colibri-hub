import { describe, expect, it } from 'vitest'
import { SharedRolePermissionGate } from './shared-role-gate'

describe('SharedRolePermissionGate', () => {
  it('binds a normalized non-zero permission replacement and applies it once with the optional reason', () => {
    const baseline = { roleName: 'Operador', description: null, permissions: [{ action: 'read', scopeId: 'scope-a' }] }
    const gate = new SharedRolePermissionGate(
      { subjectId: 'role-1', subjectVersion: 4, authorityGeneration: '7' },
      baseline,
    )
    const next = [{ action: 'write', scopeId: 'scope-a' }, { action: 'read', scopeId: 'scope-a' }]
    const draft = { ...baseline, permissions: next }

    const normalized = [...next].reverse()
    expect(gate.previewRequest(draft, 'approved')).toMatchObject({ path: '/access/roles/role-1/preview', method: 'POST', body: { permissions: normalized.map(({ action, scopeId }) => ({ action, scope_id: scopeId })) } })
    expect(gate.acceptPreview({ subjectVersion: 4 }, { ...baseline, permissions: [...next].reverse() }, 'approved', gate.currentRequestGeneration())).toBe(true)
    expect(gate.confirm()).toBe(true)
    expect(gate.applyRequest()).toEqual({ path: '/access/roles/role-1', method: 'PUT', body: { role_name: 'Operador', description: null, permissions: normalized.map(({ action, scopeId }) => ({ action, scope_id: scopeId })), expected_version: 4, reason: 'approved' } })
    expect(gate.applyRequest()).toBeNull()
  })

  it('blocks zero delta and invalidates stale previews without replaying them', () => {
    const baseline = { roleName: 'Operador', description: null, permissions: [{ action: 'read', scopeId: 'scope-a' }] }
    const gate = new SharedRolePermissionGate(
      { subjectId: 'role-1', subjectVersion: 4, authorityGeneration: '7' },
      baseline,
    )

    expect(gate.previewRequest(baseline, '')).toBeNull()
    const draft = { ...baseline, permissions: [{ action: 'write', scopeId: 'scope-a' }] }
    gate.previewRequest(draft, '')
    expect(gate.acceptPreview({ subjectVersion: 4 }, draft, '', gate.currentRequestGeneration() + 1)).toBe(false)
    expect(gate.acceptPreview({ subjectVersion: 4 }, draft, '', gate.currentRequestGeneration())).toBe(true)
    gate.invalidate()
    expect(gate.applyRequest()).toBeNull()
  })
})
