export type ApiFieldError = Readonly<{
  path: string
  message: string
}>

export type ApiErrorKind = 'aborted' | 'network' | 'http' | 'invalid_response'

export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status?: number
  readonly code?: string
  readonly fields: readonly ApiFieldError[]

  constructor({
    kind,
    message,
    status,
    code,
    fields = [],
  }: {
    kind: ApiErrorKind
    message: string
    status?: number
    code?: string
    fields?: readonly ApiFieldError[]
  }) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = status
    this.code = code
    this.fields = fields
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

export function parseApiErrorPayload(payload: unknown): Pick<ApiError, 'code' | 'fields' | 'message'> {
  if (!isRecord(payload) || !isRecord(payload.error)) {
    return { message: 'The request could not be completed.', fields: [] }
  }

  const { code, fields, message } = payload.error
  return {
    code: typeof code === 'string' ? code : undefined,
    message: typeof message === 'string' ? message : 'The request could not be completed.',
    fields: Array.isArray(fields)
      ? fields.flatMap((field) =>
          isRecord(field) && typeof field.path === 'string' && typeof field.message === 'string'
            ? [{ path: field.path, message: field.message }]
            : [],
        )
      : [],
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}
