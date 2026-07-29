import { ApiError, parseApiErrorPayload } from './httpError'

const API_BASE_PATH = '/api/v1'

export interface HttpJsonOptions {
  method?: 'GET' | 'POST'
  body?: unknown
  signal?: AbortSignal
  headers?: HeadersInit
}

export async function httpJson<T>(path: string, options: HttpJsonOptions = {}): Promise<T> {
  const response = await request(path, options)

  if (!response.ok) {
    const payload = await readJson(response)
    const error = parseApiErrorPayload(payload)
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
    return await fetch(`${API_BASE_PATH}${path}`, {
      method,
      signal,
      headers: body === undefined ? headers : { 'Content-Type': 'application/json', ...headers },
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
