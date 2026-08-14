import { describe, expect, it } from 'vitest'
import { captureAdministrationOrigin, decodeAdministrationOrigin, encodeAdministrationOrigin, recoverAdministrationRoute, resolveDiscard } from './route-state'

describe('administration route state', () => {
  it('restores the exact captured origin after a confirmed discard and preserves a dirty draft on decline', () => {
    const origin = captureAdministrationOrigin({ family: 'roles', criteria: { active: 'true' }, page: 2, subjectId: 'role-1' })

    expect(resolveDiscard(origin, false)).toEqual({ action: 'preserve' })
    expect(resolveDiscard(origin, true)).toEqual({ action: 'restore', route: origin })
  })

  it('recovers stale details and empty pages to their nearest permitted collection state', () => {
    expect(recoverAdministrationRoute({ family: 'users', criteria: { query: 'Ada' }, page: 3, subjectId: 'missing' }, 'stale')).toEqual({
      family: 'users', criteria: { query: 'Ada' }, page: 3,
    })
  })

  it('round-trips a complete origin and rejects invalid URL state', () => {
    const origin = { family: 'roles' as const, criteria: { q: 'spinner', active: 'true' }, page: 4, subjectId: 'role-1' }
    expect(decodeAdministrationOrigin(encodeAdministrationOrigin(origin))).toEqual(origin)
    expect(decodeAdministrationOrigin('{"family":"roles"}')).toBeNull()
  })

  it.each(['missing', 'denied', 'stale', 'invalid', 'aborted'] as const)('recovers %s outcomes without retaining a protected subject', (reason) => {
    expect(recoverAdministrationRoute({ family: 'roles', criteria: { q: 'ops' }, page: 2, subjectId: 'secret-role', mode: 'edit' }, reason)).toEqual({
      family: 'roles', criteria: { q: 'ops' }, page: 2,
    })
  })
})
