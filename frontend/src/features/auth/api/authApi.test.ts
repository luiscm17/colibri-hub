import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/api/httpError'
import {
  disableAuthenticationAccount,
  enableAuthenticationAccount,
  fetchAuthenticationAccount,
  fetchAuthenticationAccounts,
  fetchCurrentAuthentication,
  mapToAccountSummary,
  provisionAuthenticationAccount,
  resetAuthenticationAccountPassword,
} from './authApi'

afterEach(() => vi.unstubAllGlobals())

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

  it('rejects a response with an unknown next step at the adapter boundary', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      account_id: 'account-1', email: 'ada@example.com', display_name: 'Ada Lovelace', status: 'active', next_step: 'admin',
    }), { status: 200, headers: { 'Content-Type': 'application/json' } })))

    await expect(fetchCurrentAuthentication()).rejects.toMatchObject({ kind: 'invalid_response' } satisfies Partial<ApiError>)
  })
})

describe('Authentication administration API', () => {
  const account = {
    account_id: 'account-1',
    email: 'ada@example.com',
    display_name: 'Ada Lovelace',
    user_code: 'ADA-1',
    status: 'active',
    version: 3,
  }

  function mockJsonResponse(payload: unknown, status = 200): ReturnType<typeof vi.fn> {
    return vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }))
  }

  function expectRequest(fetchMock: ReturnType<typeof vi.fn>, path: string, body?: unknown): void {
    expect(fetchMock).toHaveBeenCalledWith(`/api/v1${path}`, expect.objectContaining({
      method: body === undefined ? 'GET' : 'POST',
      body: body === undefined ? undefined : JSON.stringify(body),
    }))
  }

  it('lists validated account responses', async () => {
    const fetchMock = mockJsonResponse([account])
    vi.stubGlobal('fetch', fetchMock)

    await expect(fetchAuthenticationAccounts()).resolves.toEqual([account])
    expectRequest(fetchMock, '/auth/accounts')
  })

  it('gets a validated account response using an encoded account ID', async () => {
    const fetchMock = mockJsonResponse(account)
    vi.stubGlobal('fetch', fetchMock)

    await expect(fetchAuthenticationAccount('account/1')).resolves.toEqual(account)
    expectRequest(fetchMock, '/auth/accounts/account%2F1')
  })

  it('provisions an account with the backend request body', async () => {
    const body = {
      email: 'ada@example.com', provisional_password: 'Provisional-123', user_code: 'ADA-1',
      display_name: 'Ada Lovelace', role_codes: ['administrator'], reason: 'New hire',
    }
    const fetchMock = mockJsonResponse(account, 201)
    vi.stubGlobal('fetch', fetchMock)

    await expect(provisionAuthenticationAccount(body)).resolves.toEqual(account)
    expectRequest(fetchMock, '/auth/accounts', body)
  })

  async function expectNoContentMutation(
    mutation: () => Promise<void>,
    path: string,
    body: unknown,
  ): Promise<void> {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(mutation()).resolves.toBeUndefined()
    expectRequest(fetchMock, path, body)
  }

  it('resets a password with its expected version and a 204 response', async () => {
    const body = { provisional_password: 'Reset-123', reason: 'Credential rotation', expected_version: 3 }
    await expectNoContentMutation(
      () => resetAuthenticationAccountPassword('account-1', body),
      '/auth/accounts/account-1/password-reset',
      body,
    )
  })

  it('disables an account with its expected version and a 204 response', async () => {
    const body = { reason: 'Leave of absence', expected_version: 3 }
    await expectNoContentMutation(
      () => disableAuthenticationAccount('account-1', body),
      '/auth/accounts/account-1/disable',
      body,
    )
  })

  it('enables an account with its expected version and a 204 response', async () => {
    const body = { provisional_password: 'Enabled-123', reason: 'Returned from leave', expected_version: 3 }
    await expectNoContentMutation(
      () => enableAuthenticationAccount('account-1', body),
      '/auth/accounts/account-1/enable',
      body,
    )
  })

  it('rejects malformed account payloads at the adapter boundary', async () => {
    vi.stubGlobal('fetch', mockJsonResponse({ ...account, version: '3' }))

    await expect(fetchAuthenticationAccount('account-1')).rejects.toMatchObject({ kind: 'invalid_response' } satisfies Partial<ApiError>)
  })

  it('rejects a non-empty lifecycle mutation response', async () => {
    vi.stubGlobal('fetch', mockJsonResponse({ ok: true }))

    await expect(disableAuthenticationAccount('account-1', { reason: 'Leave of absence', expected_version: 3 }))
      .rejects.toMatchObject({ kind: 'invalid_response' } satisfies Partial<ApiError>)
  })
})
