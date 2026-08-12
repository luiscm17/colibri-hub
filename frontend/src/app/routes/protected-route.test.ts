import { describe, expect, it } from 'vitest'
import { resolveProtectedRoute } from './protected-route-state'
import type { AccessState } from '@/features/access-control'

const allowed: AccessState = {
  status: 'ready',
  snapshot: {
    userId: 'user-1', userCode: 'USR-1', displayName: 'User', authorizationVersion: 1,
    allows: (requirement) => 'action' in requirement && requirement.action === 'read' && requirement.scope === 'warehouse.raw_materials',
  },
}

describe('protected routes', () => {
  it('fails closed until the canonical Access state is ready and allowed', () => {
    expect(resolveProtectedRoute({ status: 'loading' }, { action: 'read', scope: 'warehouse.raw_materials' })).toBe('loading')
    expect(resolveProtectedRoute({ status: 'blocked', reason: 'profile_inactive' }, { action: 'read', scope: 'warehouse.raw_materials' })).toBe('blocked')
    expect(resolveProtectedRoute({ status: 'unavailable', retryable: true }, { action: 'read', scope: 'warehouse.raw_materials' })).toBe('unavailable')
    expect(resolveProtectedRoute(allowed, { action: 'read', scope: 'warehouse.finished_products' })).toBe('denied')
    expect(resolveProtectedRoute(allowed, { action: 'read', scope: 'warehouse.raw_materials' })).toBe('allowed')
  })

  it('uses the same decision for direct and history navigation', () => {
    const requirement = { action: 'read', scope: 'warehouse.finished_products' } as const
    expect(resolveProtectedRoute(allowed, requirement)).toBe('denied')
    expect(resolveProtectedRoute(allowed, requirement)).toBe('denied')
  })
})
