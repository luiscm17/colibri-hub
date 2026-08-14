import { describe, expect, it } from 'vitest'
import { resolveAdministrationOperation } from './operations'

describe('administration operation matrix', () => {
  it('reconstructs supported direct-entry operations', () => {
    expect(resolveAdministrationOperation('roles', 'role-1')).toMatchObject({
      family: 'roles',
      endpoint: '/access/roles',
      request: 'detail',
    })
    expect(resolveAdministrationOperation('history')).toMatchObject({
      family: 'history',
      endpoint: '/access/audits',
      request: 'collection',
    })
  })

  it('default-denies prohibited administration states', () => {
    expect(resolveAdministrationOperation('scopes', 'scope-1')).toBeNull()
    expect(resolveAdministrationOperation('history', 'audit-1')).toBeNull()
    expect(resolveAdministrationOperation('users', 'new')).toBeNull()
    expect(resolveAdministrationOperation('roles', 'new')).toMatchObject({ request: 'none', renderer: 'role-create' })
    expect(resolveAdministrationOperation('presets', 'new')).toMatchObject({ request: 'none', renderer: 'preset-create' })
    expect(resolveAdministrationOperation('presets', 'preset-1', 'edit')).toMatchObject({ request: 'detail', renderer: 'preset-edit' })
    expect(resolveAdministrationOperation('users', 'user-1', 'edit')).toBeNull()
    expect(resolveAdministrationOperation('unknown')).toBeNull()
  })
})
