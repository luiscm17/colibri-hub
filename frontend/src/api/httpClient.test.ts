import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from './httpError'
import { clearAccessDeniedRecoveryHandler, clearAuthenticationRequiredHandler, httpJson, setAccessDeniedRecoveryHandler, setAuthenticationRequiredHandler } from './httpClient'

describe('httpJson protected denial recovery', () => {
  afterEach(() => {
    clearAccessDeniedRecoveryHandler()
    clearAuthenticationRequiredHandler()
    vi.unstubAllGlobals()
  })

  it('refreshes once and never replays a denied mutation', async () => {
    const recover = vi.fn().mockResolvedValue(undefined)
    const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'access_denied' }), { status: 403 }))
    setAccessDeniedRecoveryHandler(recover)
    vi.stubGlobal('fetch', fetch)

    await expect(httpJson('/warehouse/bales', {
      method: 'POST',
      body: { shipment_number: 'RM-1' },
      recoverAccessDenied: true,
    })).rejects.toMatchObject({ status: 403, code: 'access_denied' } satisfies Partial<ApiError>)

    expect(recover).toHaveBeenCalledTimes(1)
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('does not recover unprotected requests', async () => {
    const recover = vi.fn()
    setAccessDeniedRecoveryHandler(recover)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 403 })))

    await expect(httpJson('/auth/me')).rejects.toMatchObject({ status: 403 } satisfies Partial<ApiError>)

    expect(recover).not.toHaveBeenCalled()
  })

  it('notifies Authentication when a protected request ends the session', async () => {
    const sessionEnded = vi.fn().mockResolvedValue(undefined)
    setAuthenticationRequiredHandler(sessionEnded)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'authentication_required' }), { status: 401 })))

    await expect(httpJson('/warehouse/bales', { recoverAccessDenied: true })).rejects.toMatchObject({ status: 401 } satisfies Partial<ApiError>)

    expect(sessionEnded).toHaveBeenCalledTimes(1)
  })
})
