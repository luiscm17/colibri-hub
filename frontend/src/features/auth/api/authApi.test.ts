import { describe, expect, it } from 'vitest'
import { mapToAccountSummary } from './authApi'

describe('mapToAccountSummary', () => {
  it('maps the canonical /auth/me response and derives avatar initials locally', () => {
    const account = mapToAccountSummary({
      account_id: 'account-1',
      email: 'ada@example.com',
      display_name: 'Ada Lovelace',
      status: 'active',
      next_step: 'load_access',
    })

    expect(account).toEqual({
      accountId: 'account-1',
      email: 'ada@example.com',
      displayName: 'Ada Lovelace',
      initials: 'AL',
    })
  })

  it('uses a stable fallback when the display name is blank', () => {
    expect(mapToAccountSummary({
      account_id: 'account-1',
      email: 'ada@example.com',
      display_name: '   ',
      status: 'active',
      next_step: 'load_access',
    }).initials).toBe('?')
  })
})
