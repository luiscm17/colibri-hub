import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AccessProvider, useAccess } from '@/features/access-control'
import { httpJson } from '@/api/httpClient'
import { useAuth } from './auth-context'
import { AuthProvider } from './AuthContext'

const providerSession = vi.hoisted(() => ({
  getAccessToken: vi.fn(),
  getSessionKey: vi.fn((session: unknown) => (
    typeof (session as { access_token?: unknown } | null)?.access_token === 'string'
      ? (session as { access_token: string }).access_token
      : null
  )),
  hasSession: vi.fn(),
  onAuthStateChange: vi.fn(),
  signIn: vi.fn(),
  signOut: vi.fn(),
}))

vi.mock('../provider/providerSession', () => providerSession)

function StateProbe() {
  const { authState, logout } = useAuth()
  const { state: accessState } = useAccess()
  const reason = authState.status === 'unauthenticated' ? authState.reason : ''
  return <>
    <output>{`${authState.status}:${reason}:${accessState.status}`}</output>
    <button onClick={() => void logout()}>Logout</button>
  </>
}

function renderProviders() {
  render(<AuthProvider><AccessProvider><StateProbe /></AccessProvider></AuthProvider>)
}

const response = (body: unknown) => new Response(JSON.stringify(body), {
  status: 200,
  headers: { 'Content-Type': 'application/json' },
})

function deferred<T>(): { promise: Promise<T>; resolve: (value: T) => void } {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise
  })
  return { promise, resolve }
}

describe('AuthProvider access handoff', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    providerSession.getAccessToken.mockResolvedValue('token')
    providerSession.onAuthStateChange.mockReturnValue({ unsubscribe: vi.fn() })
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('publishes unavailable when provider session restoration fails without loading access', async () => {
    providerSession.hasSession.mockRejectedValue(new Error('provider unavailable'))
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    renderProviders()

    expect(await screen.findByText('unavailable::unavailable')).toBeTruthy()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('fails closed when /auth/me is malformed and does not start access', async () => {
    providerSession.hasSession.mockResolvedValue(true)
    const fetchMock = vi.fn().mockResolvedValue(response({
      account_id: 'account-1', email: 'ada@example.com', display_name: 'Ada Lovelace', status: 'active', next_step: 'unknown',
    }))
    vi.stubGlobal('fetch', fetchMock)

    renderProviders()

    expect(await screen.findByText('unauthenticated:denied:waiting-for-authentication')).toBeTruthy()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('keeps the valid load_access handoff behavior unchanged', async () => {
    providerSession.hasSession.mockResolvedValue(true)
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      if (String(input).endsWith('/auth/me')) return Promise.resolve(response({
        account_id: 'account-1', email: 'ada@example.com', display_name: 'Ada Lovelace', status: 'active', next_step: 'load_access',
      }))
      if (String(input).endsWith('/access/me')) return Promise.resolve(response({
        user_id: 'user-1', user_code: 'ADA-1', display_name: 'Ada Lovelace', is_active: true,
        authorization: { version: 1, is_global: true, actions: ['read'], permissions: [] },
      }))
      throw new Error(`Unexpected request: ${String(input)}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    renderProviders()

    await waitFor(() => expect(screen.getByText('authenticated::ready')).toBeTruthy())
    expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/access/me'))).toHaveLength(1)
  })

  it('does not restore authentication from a validation that completes after provider sign-out', async () => {
    providerSession.hasSession.mockResolvedValue(true)
    let resolveAuthentication: ((value: Response) => void) | undefined
    const fetchMock = vi.fn(() => new Promise<Response>((resolve) => {
      resolveAuthentication = resolve
    }))
    vi.stubGlobal('fetch', fetchMock)

    renderProviders()

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    const onAuthStateChange = (providerSession.onAuthStateChange as unknown as {
      mock: { calls: Array<[(event: string) => void]> }
    }).mock.calls[0]?.[0]
    expect(onAuthStateChange).toBeDefined()
    if (!onAuthStateChange) throw new Error('Expected an auth state callback')
    onAuthStateChange('SIGNED_OUT')
    resolveAuthentication?.(response({
      account_id: 'account-1', email: 'ada@example.com', display_name: 'Ada Lovelace', status: 'active', next_step: 'load_access',
    }))

    expect(await screen.findByText('unauthenticated:expired:waiting-for-authentication')).toBeTruthy()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('publishes only the latest provider session validation and one Access bootstrap', async () => {
    providerSession.hasSession.mockResolvedValue(false)
    const first = deferred<Response>()
    const second = deferred<Response>()
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      if (String(input).endsWith('/auth/me')) {
        return fetchMock.mock.calls.filter(([request]) => String(request).endsWith('/auth/me')).length === 1
          ? first.promise
          : second.promise
      }
      if (String(input).endsWith('/access/me')) return Promise.resolve(response({
        user_id: 'user-1', user_code: 'ADA-1', display_name: 'Ada Lovelace', is_active: true,
        authorization: { version: 1, is_global: true, actions: ['read'], permissions: [] },
      }))
      throw new Error(`Unexpected request: ${String(input)}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    renderProviders()
    await screen.findByText('unauthenticated:undefined:waiting-for-authentication')
    const onAuthStateChange = (providerSession.onAuthStateChange as unknown as {
      mock: { calls: Array<[(event: string, session: unknown) => void]> }
    }).mock.calls[0]?.[0]
    if (!onAuthStateChange) throw new Error('Expected an auth state callback')
    onAuthStateChange('SIGNED_IN', { access_token: 'first-token' })
    onAuthStateChange('TOKEN_REFRESHED', { access_token: 'second-token' })
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))

    second.resolve(response({
      account_id: 'account-2', email: 'grace@example.com', display_name: 'Grace Hopper', status: 'active', next_step: 'load_access',
    }))
    await waitFor(() => expect(screen.getByText('authenticated::ready')).toBeTruthy())
    first.resolve(response({
      account_id: 'account-1', email: 'ada@example.com', display_name: 'Ada Lovelace', status: 'active', next_step: 'load_access',
    }))
    await waitFor(() => expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/access/me'))).toHaveLength(1))
  })

  it('finishes local logout when provider sign-out fails and clears the token accessor', async () => {
    providerSession.hasSession.mockResolvedValue(false)
    providerSession.signOut.mockRejectedValue(new Error('provider unavailable'))
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      void init
      if (String(input).endsWith('/auth/session')) return Promise.resolve(new Response(null, { status: 204 }))
      if (String(input).endsWith('/token-check')) return Promise.resolve(response({ ok: true }))
      throw new Error(`Unexpected request: ${String(input)}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    renderProviders()
    await screen.findByText('unauthenticated:undefined:waiting-for-authentication')
    screen.getByRole('button', { name: 'Logout' }).click()

    expect(await screen.findByText('unauthenticated:logged-out:waiting-for-authentication')).toBeTruthy()
    await httpJson('/token-check')
    expect(providerSession.signOut).toHaveBeenCalledTimes(1)
    expect(fetchMock.mock.calls[1]?.[1]?.headers).toEqual({})
  })

  it('ends the session as expired when /auth/me returns authentication-required', async () => {
    providerSession.hasSession.mockResolvedValue(true)
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      code: 'authentication_required', message: 'Session expired',
    }), { status: 401, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)

    renderProviders()

    expect(await screen.findByText('unauthenticated:expired:waiting-for-authentication')).toBeTruthy()
    expect(providerSession.signOut).toHaveBeenCalledTimes(1)
  })
})
