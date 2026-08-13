import { describe, expect, it } from 'vitest'
import {
  activeRoleIds,
  availablePermissionPairs,
  effectivePermissions,
  isSelectablePermission,
  permissionReferenceState,
} from './matrix'

const scopes = [
  { scopeId: 'warehouse', scopeCode: 'warehouse.raw_materials', isActive: true, supportedActions: ['read', 'write'] },
  { scopeId: 'legacy', scopeCode: 'warehouse.legacy', isActive: false, supportedActions: ['read'] },
]

describe('permission selection matrix', () => {
  it('unions permissions from active roles by stable IDs only', () => {
    const roles = [
      { roleId: 'operator', isActive: true, permissions: [{ action: 'read', scopeCode: 'warehouse.raw_materials' }] },
      { roleId: 'quality', isActive: true, permissions: [{ action: 'write', scopeCode: 'warehouse.raw_materials' }] },
      { roleId: 'retired', isActive: false, permissions: [{ action: 'read', scopeCode: 'warehouse.legacy' }] },
    ]

    expect(activeRoleIds(roles)).toEqual(['operator', 'quality'])
    expect(effectivePermissions(roles)).toEqual([
      { action: 'read', scopeCode: 'warehouse.raw_materials' },
      { action: 'write', scopeCode: 'warehouse.raw_materials' },
    ])
  })

  it('offers only exact supported action and active scope pairs', () => {
    expect(availablePermissionPairs(scopes)).toEqual([
      { action: 'read', scopeCode: 'warehouse.raw_materials' },
      { action: 'write', scopeCode: 'warehouse.raw_materials' },
    ])
    expect(isSelectablePermission({ action: 'read', scopeCode: 'warehouse.raw_materials' }, scopes)).toBe(true)
    expect(isSelectablePermission({ action: 'manage_access', scopeCode: 'warehouse.raw_materials' }, scopes)).toBe(false)
    expect(isSelectablePermission({ action: 'read', scopeCode: 'warehouse.legacy' }, scopes)).toBe(false)
    expect(isSelectablePermission({ action: 'read', scopeCode: 'warehouse' }, scopes)).toBe(false)
  })

  it('does not use labels as authorization facts', () => {
    const renamedScope = [{ ...scopes[0], scopeName: 'Different presentation label' }]

    expect(isSelectablePermission({ action: 'write', scopeCode: 'warehouse.raw_materials' }, renamedScope)).toBe(true)
  })

  it('accepts new catalog pairs without enumerating action or scope names', () => {
    const expandedCatalog = [...scopes, {
      scopeId: 'spinning', scopeCode: 'yarn_spinning.quality', isActive: true, supportedActions: ['approve'],
    }]

    expect(isSelectablePermission({ action: 'approve', scopeCode: 'yarn_spinning.quality' }, expandedCatalog)).toBe(true)
  })

  it('keeps inactive references removable while unsupported extensions remain unavailable', () => {
    expect(permissionReferenceState({ action: 'read', scopeCode: 'warehouse.legacy' }, scopes)).toBe('inactive')
    expect(permissionReferenceState({ action: 'delete', scopeCode: 'warehouse.raw_materials' }, scopes)).toBe('unsupported')
    expect(permissionReferenceState({ action: 'read', scopeCode: 'unknown.scope' }, scopes)).toBe('unsupported')
  })
})
