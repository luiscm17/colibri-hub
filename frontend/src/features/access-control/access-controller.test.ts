import { ApiError } from '@/api/httpError'
import { describe, expect, it } from 'vitest'
import {
  AccessController,
  createAccessSnapshot,
  type AccessHandoff,
  type AccessMeFetcher,
} from './access-controller'

const eligibleHandoff: AccessHandoff = {
  condition: 'eligible',
  accountId: 'account-1',
  handoffId: 'handoff-1',
}

const ordinaryResponse = {
  user_id: 'user-1',
  user_code: 'USR-1',
  display_name: 'Jane Doe',
  is_active: true,
  roles: [],
  authorization: {
    is_global: false,
    actions: [],
    permissions: [{ action: 'read', scope_code: 'warehouse.raw_materials' }],
    version: 1,
  },
}

function deferred<T>(): { promise: Promise<T>; resolve: (value: T) => void } {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise
  })
  return { promise, resolve }
}

function fetcher(response: unknown = ordinaryResponse): AccessMeFetcher {
  return async () => response
}

describe('AccessController', () => {
  it('only starts access for an eligible Authentication handoff and clears other conditions', async () => {
    const controller = new AccessController(fetcher())

    await controller.acceptHandoff({ condition: 'unresolved' })
    expect(controller.getState()).toEqual({ status: 'waiting-for-authentication' })

    await controller.acceptHandoff({ condition: 'password-change-required' })
    expect(controller.getState()).toEqual({ status: 'waiting-for-authentication' })

    await controller.acceptHandoff({ condition: 'ended' })
    expect(controller.getState()).toEqual({ status: 'waiting-for-authentication' })

    await controller.acceptHandoff({ condition: 'unavailable', retryable: true })
    expect(controller.getState()).toEqual({ status: 'unavailable', retryable: true })

    await controller.acceptHandoff(eligibleHandoff)
    expect(controller.getState().status).toBe('ready')
  })

  it('retries eligible access after a recoverable failure and suppresses duplicate handoffs', async () => {
    const requests: AbortSignal[] = []
    const getAccess: AccessMeFetcher = async (signal) => {
      requests.push(signal)
      if (requests.length === 1) {
        throw new ApiError({ kind: 'network', message: 'offline' })
      }
      return ordinaryResponse
    }
    const controller = new AccessController(getAccess)

    await controller.acceptHandoff(eligibleHandoff)
    expect(controller.getState()).toEqual({ status: 'unavailable', retryable: true })

    await controller.acceptHandoff(eligibleHandoff)
    expect(requests).toHaveLength(1)

    await controller.retry()
    expect(requests).toHaveLength(2)
    expect(controller.getState().status).toBe('ready')
  })

  it('maps complete ordinary and global grants with exact, compound decisions', () => {
    const ordinary = createAccessSnapshot(ordinaryResponse)
    const global = createAccessSnapshot({
      ...ordinaryResponse,
      authorization: { is_global: true, actions: ['read'], permissions: [], version: 2 },
    })

    expect(ordinary?.allows({ action: 'read', scope: 'warehouse.raw_materials' })).toBe(true)
    expect(ordinary?.allows({ action: 'read', scope: 'warehouse.raw' })).toBe(false)
    expect(ordinary?.allows({ action: 'write', scope: 'warehouse.raw_materials' })).toBe(false)
    expect(ordinary?.allows({ allOf: [{ action: 'read', scope: 'warehouse.raw_materials' }, { action: 'write', scope: 'warehouse.raw_materials' }] })).toBe(false)
    expect(ordinary?.allows({ anyOf: [{ action: 'write', scope: 'warehouse.raw_materials' }, { action: 'read', scope: 'warehouse.raw_materials' }] })).toBe(true)
    expect(global?.allows({ action: 'read', scope: 'anything.at.all' })).toBe(true)
    expect(global?.allows({ action: 'write', scope: 'anything.at.all' })).toBe(false)
  })

  it('fails closed for malformed variants and normalizes backend outcomes', async () => {
    expect(createAccessSnapshot({ ...ordinaryResponse, authorization: { is_global: false, actions: ['read'], permissions: [], version: 1 } })).toBeNull()
    expect(createAccessSnapshot({ ...ordinaryResponse, authorization: { is_global: true, actions: ['read'], permissions: [{ action: 'read', scope_code: 'x' }], version: 1 } })).toBeNull()
    expect(createAccessSnapshot({ ...ordinaryResponse, authorization: { is_global: true, actions: ['invalid'], permissions: [], version: 1 } })).toBeNull()
    expect(createAccessSnapshot({ ...ordinaryResponse, authorization: { global: false, actions: [], permissions: [], version: 1 } })).toBeNull()

    for (const [error, expected] of [
      [new ApiError({ kind: 'http', status: 404, code: 'profile_not_found', message: 'missing' }), 'blocked'],
      [new ApiError({ kind: 'http', status: 403, code: 'profile_inactive', message: 'inactive' }), 'blocked'],
      [new ApiError({ kind: 'http', status: 403, message: 'denied' }), 'unavailable'],
      [new ApiError({ kind: 'http', status: 401, message: 'unauthorized' }), 'waiting-for-authentication'],
      [new ApiError({ kind: 'network', message: 'offline' }), 'unavailable'],
    ] as const) {
      const controller = new AccessController(async () => { throw error })
      await controller.acceptHandoff(eligibleHandoff)
      expect(controller.getState().status).toBe(expected)
    }

    const invalid = new AccessController(fetcher({ invalid: true }))
    await invalid.acceptHandoff(eligibleHandoff)
    expect(invalid.getState()).toEqual({ status: 'unavailable', retryable: true })
  })

  it('aborts obsolete requests and only atomically publishes the newest generation', async () => {
    const first = deferred<unknown>()
    const second = deferred<unknown>()
    const signals: AbortSignal[] = []
    const controller = new AccessController((signal) => {
      signals.push(signal)
      return signals.length === 1 ? first.promise : second.promise
    })

    const firstLoad = controller.acceptHandoff(eligibleHandoff)
    const secondLoad = controller.refresh()
    expect(signals[0]?.aborted).toBe(true)

    second.resolve({ ...ordinaryResponse, authorization: { ...ordinaryResponse.authorization, version: 2 } })
    await secondLoad
    first.resolve(ordinaryResponse)
    await firstLoad

    expect(controller.getState()).toMatchObject({ status: 'ready', snapshot: { authorizationVersion: 2 } })
    controller.clear()
    expect(controller.getState()).toEqual({ status: 'waiting-for-authentication' })
  })
})
