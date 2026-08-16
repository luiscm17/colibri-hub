import { describe, expect, it } from 'vitest'
import { toPermissionInputs } from './permission-adapter'

describe('toPermissionInputs', () => {
  it('joins known scope codes to ids while selection policy remains separate', () => {
    expect(toPermissionInputs(
      [{ action: 'read', scopeCode: 'warehouse' }, { action: 'write', scopeCode: 'inactive' }],
      [{ scopeId: 'scope-1', scopeCode: 'warehouse', isActive: true }, { scopeId: 'scope-2', scopeCode: 'inactive', isActive: false }],
    )).toEqual([{ action: 'read', scope_id: 'scope-1' }, { action: 'write', scope_id: 'scope-2' }])
  })
})
