import { ApiError, parseApiErrorPayload } from './httpError'

const API_BASE_PATH = '/api/v1'

type TokenAccessor = () => Promise<string | null>
type AccessDeniedRecoveryHandler = () => Promise<void>
type AuthenticationRequiredHandler = () => Promise<void>

let tokenAccessor: TokenAccessor | null = null
let accessDeniedRecoveryHandler: AccessDeniedRecoveryHandler | null = null
let authenticationRequiredHandler: AuthenticationRequiredHandler | null = null

export function setTokenAccessor(accessor: TokenAccessor): void {
  tokenAccessor = accessor
}

export function clearTokenAccessor(): void {
  tokenAccessor = null
}

export function setAccessDeniedRecoveryHandler(handler: AccessDeniedRecoveryHandler): void {
  accessDeniedRecoveryHandler = handler
}

export function clearAccessDeniedRecoveryHandler(): void {
  accessDeniedRecoveryHandler = null
}

export function setAuthenticationRequiredHandler(handler: AuthenticationRequiredHandler): void {
  authenticationRequiredHandler = handler
}

export function clearAuthenticationRequiredHandler(): void {
  authenticationRequiredHandler = null
}

export interface HttpJsonOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
  headers?: HeadersInit
  recoverAccessDenied?: boolean
}

export async function httpJson<T>(path: string, options: HttpJsonOptions = {}): Promise<T> {
  const response = await request(path, options)

  if (!response.ok) {
    const payload = await readJson(response)
    const error = parseApiErrorPayload(payload)
    if (response.status === 401 || error.code === 'authentication_required') {
      await authenticationRequiredHandler?.()
    }
    if (response.status === 403 && options.recoverAccessDenied) {
      await accessDeniedRecoveryHandler?.()
    }
    throw new ApiError({ kind: 'http', status: response.status, ...error })
  }

  if (response.status === 204) {
    return undefined as T
  }

  const payload = await readJson(response)
  if (payload === undefined) {
    throw new ApiError({
      kind: 'invalid_response',
      status: response.status,
      message: 'The server returned an invalid response.',
    })
  }
  return payload as T
}

async function request(path: string, { method = 'GET', body, signal, headers }: HttpJsonOptions): Promise<Response> {
  try {
    const resolvedHeaders: Record<string, string> = {}

    if (body !== undefined) {
      resolvedHeaders['Content-Type'] = 'application/json'
    }

    if (tokenAccessor) {
      const token = await tokenAccessor()
      if (token) {
        resolvedHeaders['Authorization'] = `Bearer ${token}`
      }
    }

    if (headers) {
      const normalized = new Headers(headers)
      normalized.forEach((value, key) => {
        resolvedHeaders[key] = value
      })
    }

    return await fetch(`${API_BASE_PATH}${path}`, {
      method,
      signal,
      headers: resolvedHeaders,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError({ kind: 'aborted', message: 'The request was cancelled.' })
    }
    throw new ApiError({ kind: 'network', message: 'The service is unavailable. Please try again.' })
  }
}

async function readJson(response: Response): Promise<unknown | undefined> {
  try {
    return await response.json()
  } catch {
    return undefined
  }
}
