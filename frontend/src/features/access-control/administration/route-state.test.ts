import { describe, expect, it } from 'vitest'
import { captureAdministrationOrigin, recoverAdministrationRoute, resolveDiscard } from './route-state'

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
    expect(recoverAdministrationRoute({ family: 'history', criteria: { change_kind: 'role_updated' }, page: 2 }, 'empty-page')).toEqual({
      family: 'history', criteria: { change_kind: 'role_updated' }, page: 1,
    })
  })
})
