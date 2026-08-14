import { describe, expect, it } from 'vitest'
import { createAdjustableRoleDraft, createAdjustableRoleRequest, createExactPresetCopy } from './presets'

const preset = {
  presetId: 'preset-1',
  presetCode: 'warehouse-operator',
  presetName: 'Warehouse operator',
  description: 'Initial template',
  permissions: [{ action: 'read', scopeCode: 'warehouse.raw_materials' }],
}

describe('preset flows', () => {
  it('uses the exact-copy contract without carrying preset permissions into the request', () => {
    expect(createExactPresetCopy(preset, {
      roleCode: 'warehouse-copy',
      roleName: 'Warehouse copy',
      description: 'Copied once',
      reason: '',
    })).toEqual({
      path: '/access/role-presets/preset-1/roles',
      method: 'POST',
      body: {
        role_code: 'warehouse-copy',
        role_name: 'Warehouse copy',
        description: 'Copied once',
        reason: '',
      },
    })
  })

  it('creates an adjustable independent role draft from a preset snapshot', () => {
    const draft = createAdjustableRoleDraft(preset, {
      roleCode: 'warehouse-adjustable',
      roleName: 'Warehouse adjustable',
    })
    preset.permissions[0].action = 'write'
    preset.description = 'Changed template'

    expect(draft).toEqual({
      sourcePresetId: 'preset-1',
      roleCode: 'warehouse-adjustable',
      roleName: 'Warehouse adjustable',
      description: 'Initial template',
      permissions: [{ action: 'read', scopeCode: 'warehouse.raw_materials' }],
    })
    expect(createAdjustableRoleRequest(draft, [{ action: 'read', scope_id: 'scope-1' }], 'Copy role')).toMatchObject({ path: '/access/roles', body: { permissions: [{ action: 'read', scope_id: 'scope-1' }] } })
  })
})
